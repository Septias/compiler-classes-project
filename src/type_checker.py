from dataclasses import dataclass
from typing import Optional

from ast_1_python import *
from util.immutable_list import IList

# Error Type

@dataclass
class TypeError(Exception):
    msg: str

# Typing context

type TCtx = dict[Id, Type]

# Type Checking

def type_check(p: Program):
    match p:
        case Program(classes, defs, body):
            ctx: TCtx = dict()
            for d in defs:
                type_declare_def(ctx, d)
            type_check_stmts(ctx, classes)
            for d in defs:
                type_check_def(ctx, d)
            type_check_stmts(ctx, body)

def type_declare_def(ctx: TCtx, d: Decl):
    match d:
        case DFun(funcvar, parameters, result_type, _):
            ftype = TCallable(IList([ty for (_, ty) in parameters]), result_type)
            if funcvar in ctx:
                raise TypeError(f"Function {funcvar} defined twice")
            ctx[funcvar] = ftype

def type_check_def(ctx: TCtx, d: Decl):
    match d:
        case DFun(funcvar, parameters, result_type, body):
            local_ctx = ctx.copy()
            local_ctx.update(parameters)
            local_ctx[Id('@ret')] = result_type
            if not type_check_stmts(local_ctx, body):
                match result_type:
                    case TNone():
                        pass
                    case _:
                        raise TypeError(f"Function {funcvar} does not return {result_type} on all paths")

def type_check_stmts(ctx: TCtx, ss: IList[Stmt]) -> bool:
    for s in ss:
        if type_check_stmt(ctx, s):
            return True
    return False

def type_check_stmt(ctx: TCtx, s: Stmt) -> bool:
    match s:
        case SExpr(e):
            _ = type_check_expr(ctx, e)
            return False
        case SPrint(e):
            te = type_check_expr(ctx, e)
            check_type_equal(te, TInt(), e)
            return False
        case SAssign(x, t, e):
            if t is None:
                te = type_check_expr(ctx, e)
                match x:
                    case EField(ex, tfieldname):
                        ty = type_check_expr(ctx, ex)
                        x.type = ty
                        super = ty
                        while super is not None:
                            match super:
                                case TClass(_, new_super, fields, _):
                                    for fieldname, fieldtype in fields:
                                        if tfieldname == fieldname:
                                            check_type_equal(te, fieldtype, s)
                                            return False
                                    super = new_super
                                case _:
                                    raise TypeError(f"can not access field of type {ty}")    
                        raise TypeError(f"cannot assign: field {tfieldname} not found for class {super.name} in {s}")
                    case Id(_):
                        if x in ctx:
                            check_type_equal(te, ctx[x], s)
                        else:
                            ctx[x] = te
                        return False
                    case _:
                        raise TypeError(f"can not assign {e} to {x}")
            # t is not None, meaning the rhs is with type annotation
            else:
                match x:
                    case Id(_):
                        if x in ctx:
                            check_type_equal(t, ctx[x], s)
                        else:
                            ctx[x] = t
                            check_expr(ctx, e, t)
                            return False
                    case _:
                        raise TypeError(f"can not assign {e} to {x}")
        case SIf(test, body, orelse):
            ttest = type_check_expr(ctx, test)
            check_type_equal(ttest, TBool(), test)
            ctx_orelse = ctx.copy()
            rt_body = type_check_stmts(ctx, body)
            rt_else = type_check_stmts(ctx_orelse, orelse)
            check_ctx_equal(ctx, ctx_orelse, s)
            return rt_body and rt_else
        case SWhile(test, body):
            ttest = type_check_expr(ctx, test)
            check_type_equal(ttest, TBool(), test)
            type_check_stmts(ctx, body)
            return False
        case SReturn(e):
            check_expr(ctx, e, ctx[Id('@ret')])
            return True
        case SRaise(e):
            check_expr(ctx, e, TInt())
            return True
        case STry(body, x, handler):
            rb = type_check_stmts(ctx, body)
            ctx[x] = TInt()
            rh = type_check_stmts(ctx, handler)
            return rb and rh
        case SClass(name, super, fields, methods):
            if name in ctx:
                raise TypeError(f"the name {name} is already in use for a class or function")
            fieldnames = []
            # make insurances over the base class
            base = super
            while base is not None:
                match base:
                    case TClass(parentname, new_base, parentfields, parentmethods):
                        if name == parentname:
                            raise TypeError(f"Class {name} can not inherit from itself")
                        if parentname not in ctx:
                            raise TypeError(f"{name} tries to inherit from not defined class {parentname}")
                        # we can assume that the fields of the parent are unique, as it was already added to ctx and thus checked
                        # we also assume that field names MUST be unique over inheritance
                        fieldnames.extend([field[0] for field in parentfields])
                        base = new_base
                    case TNone() | TTuple() | TCallable() as obj:
                        raise TypeError(f"Type {type(obj).__name__} is not an acceptable base type")
                    case TBool() | TInt():
                        raise TypeError(f"{name} tries to inherit from a primitive type but this is forbidden")
                    case _:
                        raise TypeError(f"non-allowed type {base} as base of {name}")
            for fieldname, _ in fields:
                if fieldname in fieldnames:
                    raise NameError(f"multiple use of {fieldname} for name of field in class {name}")
                fieldnames.append(fieldname)
            # type check method definitions
            methodnames = []
            for method in methods:
                if method.name in methodnames:
                    raise NameError(f"multiple use of {method.name} for name of method in class {name}")
                if method.name in fieldnames:
                    raise NameError(f"method name {method.name} is already in use for a field in class {name} or its parents")
                match method.params[0]:
                    case (Id("self"), TClass(_, _, _, _)):
                        pass
                    case _:
                        raise TypeError(f"first argument of method {method.name} from class {name} is not self")     
                methodnames.append(method.name)
            methods_types = [(method.name, TCallable(IList([a[1] for a in method.params]), method.ret_ty)) for method in methods]
            class_type = TClass(name, super, fields, IList(methods_types))
            ctx[name] = class_type
            # go over all methods again and annotate the selfs
            for method in methods:
                method.params[0][1].fields = class_type.fields
                method.params[0][1].methods = class_type.methods
                type_check_def(ctx, method)
            # return value should only be True if we return from a method or statement
            return False

# infer type of an expression        
def type_check_expr(ctx: TCtx, e: Expr) -> Type:
    match e:
        case EConst(x):
            match x:
                case None:
                    return TNone()
                case bool(_):
                    return TBool()
                case int(_):
                    if x >= 2 ** 62 or x < -(2 ** 62):
                        raise TypeError(f"Integer constant {x} is too large for 63bit.")
                    else:
                        return TInt()
        case EVar(x):
            if x in ctx:
                return ctx[x]
            else:
                raise TypeError(f"Undefined variable {x}.")
        case EOp1(op, e):
            te = type_check_expr(ctx, e)
            match op:
                case "-":
                    check_type_equal(te, TInt(), e)
                    return TInt()
                case "not":
                    check_type_equal(te, TBool(), e)
                    return TBool()
        case EOp2(e1, op, e2):
            t1 = type_check_expr(ctx, e1)
            t2 = type_check_expr(ctx, e2)
            if type(t1) is TTuple or type(t2) is TTuple:
                match op:
                    case "is":
                        check_type_equal(t1, t2, e)
                        return TBool()
                    case _:
                        raise TypeError(f"Operator '{op}' is not supported for tuples.")
            match op:
                case "+" | "-":
                    check_type_equal(t1, TInt(), e1)
                    check_type_equal(t2, TInt(), e2)
                    return TInt()
                case "==" | "!=":
                    check_type_equal(t1, t2, e)
                    return TBool()
                case "<=" | "<" | ">" | ">=":
                    check_type_equal(t1, TInt(), e1)
                    check_type_equal(t2, TInt(), e2)
                    return TBool()
                case "and" | "or":
                    check_type_equal(t1, TBool(), e1)
                    check_type_equal(t2, TBool(), e2)
                    return TBool()
                case "is":
                    raise TypeError("Operator 'is' used on expression of non-tuple type")
        case EInput():
            return TInt()
        case EIf(test, body, orelse):
            ttest = type_check_expr(ctx, test)
            tbody = type_check_expr(ctx, body)
            torelse = type_check_expr(ctx, orelse)
            check_type_equal(ttest, TBool(), test)
            check_type_equal(tbody, torelse, e)
            return tbody
        case ETuple(es):
            return TTuple(IList([type_check_expr(ctx, e) for e in es]))
        case ETupleAccess(e, i):
            t = type_check_expr(ctx, e)
            match t:
                case TTuple(ts):
                    if 0 <= i < len(ts):
                        return ts[i]
                    else:
                        raise TypeError(f"Index {i} is out of bounds for tuple of length {len(ts)}.")
                case t:
                    raise TypeError(f"Tuple access on non-tuple type {t}.")
        case ETupleLen(e):
            t = type_check_expr(ctx, e)
            match t:
                case TTuple(ts):
                    return TInt()
                case t:
                    raise TypeError(f"Tuple length used on non-tuple type {t}.")
        case ECall(f, es):
            fty = type_check_expr(ctx, f)
            match fty:
                # function call
                case TCallable(arg_tys, res_ty):
                    if len(es) != len(arg_tys):
                        raise TypeError(f"Calling function with wrong number of arguments {e}")
                    for (e, ty) in zip(es, arg_tys):
                        check_expr(ctx, e, ty)
                    return res_ty
                # constructor call
                case TClass(name, super, fields, _):
                    membervars = [x for x in fields]
                    while super is not None:
                        match super:
                            case TClass(_, new_super, new_fields, _):
                                membervars = [x for x in new_fields] + membervars
                                super = new_super
                            case _:
                                raise TypeError(f"{name} has illegal super {super}")
                    if len(es) != len(membervars):
                        raise TypeError(f"Constructor of Class {name} called with wrong number of arguments(got {len(es)}, exprected {len(membervars)})")
                    field_tys = [attr[1] for attr in membervars]
                    for (e, ty) in zip(es, field_tys):
                        check_expr(ctx, e, ty)
                    return fty
                case t:
                    raise TypeError(f"Calling non-function type {t}")
        case ELambda():
            raise TypeError(f"Cannot synthesize type of {pretty_expr(e)}")
        case EField(expr, fieldname):
            exprtype = type_check_expr(ctx, expr)
            e.type = exprtype
            super = exprtype
            while super is not None:
                match super:
                    case TClass(_, new_super, fields, _):
                        for (name, fieldtype) in fields:
                            if name == fieldname:
                                return fieldtype
                        super = new_super
                    case TInt() | TBool() | TCallable() | TTuple() | TNone():
                        raise TypeError(f"Illegal parent type for {exprtype}")
            raise NameError(f"Cannot find a field with the name {fieldname} in class {exprtype}")
        case EMethod(expr, name, args):
            exprtype = type_check_expr(ctx, expr)
            match exprtype:
                case TClass(classname, base, fields, methods):
                    # go from neares class (self) to most distance parent class
                    seen_methods = [m[0] for m in methods]
                    # the bool represents origin True = Method, False = member variable lambda
                    all_methods: list[tuple[tuple[Id, TCallable], bool]] = [(m, True) for m in methods]
                    for field in fields:
                        if field[0] not in seen_methods:
                            match field[1]:
                                case TCallable():
                                    seen_methods.append(field[0])
                                    all_methods.append((field, False))
                    while base is not None:
                        match base:
                            case TClass(scname, scbase, scfields, scmethods):
                                for scmethod in scmethods:
                                    if scmethod[0] not in seen_methods:
                                        seen_methods.append(scmethod[0])
                                        all_methods.append((scmethod, True))
                                for scfield in scfields:
                                    if scmethod[0] not in seen_methods:
                                        match scfield[1]:
                                            case TCallable():
                                                seen_methods.append(scfield[0])
                                                all_methods.append((scfield, False))
                                base = scbase
                            case _:
                                base = None
                    if len(all_methods) == 0:
                        raise TypeError(f"could not find any methods associated with {classname}")
                    e.type = exprtype
                    for (mname, mtype), from_method in all_methods:
                        if mname == name:
                            # this is only the case, if we have a Lambda member variable which takes no args
                            if len(mtype.param_tys) == 0:
                                m_arg_types = IList([])
                            else:
                                # if it came from a method we remove the implicit self (no need to check, will be inserted in a later compilation step)
                                if from_method:
                                    m_arg_types = mtype.param_tys[1:]
                                else:
                                    m_arg_types = mtype.param_tys
                            if len(args) != len(m_arg_types):
                                raise TypeError(f"{classname}.{name} expected {len(m_arg_types)} arguments but got {len(args)}")
                            # check argument types
                            for i, arg in enumerate(args):
                                check_expr(ctx, arg, m_arg_types[i])
                                #arg_ty = type_check_expr(ctx, arg)
                                #check_type_equal(arg_ty, m_arg_types[i], e)
                            return mtype.ret_ty
                    raise NameError(f"could not find method {name}")
                case _:
                    raise TypeError(f"expected class type but got {exprtype}")
        # case EArity(e):
        #     te = type_check_expr(ctx, e)
        #     match te:
        #         case TCallable():
        #             return TInt()
        #         case _:
        #             raise TypeError(f"Arity expects a function in {pretty_expr(e)}")

# check expression against given type
def check_expr(ctx: TCtx, e: Expr, ty: Type):
    match e:
        case ELambda(xs, body):
            match ty:
                case TCallable(arg_tys, ret_ty):
                    if len(xs) != len(arg_tys):
                        raise TypeError(f"Wrong number of arguments: {pretty_expr(e)} - {pretty_type(ty)}")
                    new_ctx = ctx.copy()
                    new_ctx.update(zip(xs, arg_tys))
                    check_expr(new_ctx, body, ret_ty)
                case _:
                    raise TypeError(f"Lambda cannot have type {pretty_type(ty)}")
        case _:
            te = type_check_expr(ctx, e)
            check_type_equal(te, ty, e)

def check_type_equal(thave: Type, texpect: Type, es: Expr | Stmt):
    match (thave, texpect):
        case (TClass(_, _, _, _), TClass(_, _, _, _)):
            want = texpect
            have = thave
            while have is not None:
                if want == have:
                    return
                have = have.super
            raise TypeError(f"class mismatch: {repr(thave.name.name)} seems to not be a subclass of {repr(texpect.name.name)} in {repr(es)}")
        case _:
            if thave != texpect:
                raise TypeError(f"I got {repr(thave)} but I expected {repr(texpect)} in {repr(es)}")

def check_ctx_equal(ctx1: TCtx, ctx2: TCtx, es: Expr | Stmt):
    for x in ctx1:
        if x in ctx2:
            check_type_equal(ctx1[x], ctx2[x], es)
        else:
            del ctx1[x]
