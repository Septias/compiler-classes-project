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
        case Program(defs, body):
            ctx: TCtx = dict()
            for d in defs:
                type_declare_def(ctx, d)
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
            te = type_check_expr(ctx, e)
            match x:
                case EField(e, tfieldname):
                    ty = type_check_expr(ctx, e)
                    match ty:
                        case TClass(classname, base, fields, methods):
                            for fieldname, fieldtype in fields:
                                if tfieldname == fieldname:
                                    check_type_equal(te, fieldtype, s)
                        case _:
                            raise TypeError(f"can not access field of type {ty}")
                    return False
                case Id(_):
                    if t is None:
                        if x in ctx:
                            check_type_equal(te, ctx[x], s)
                        else:
                            ctx[x] = te
                        return False
                    else:
                        if x in ctx:
                            check_type_equal(t, ctx[x], s)
                        else:
                            ctx[x] = t
                        check_expr(ctx, e, t)
                        return False
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
        # TODO: check if this is correct
        case SClass(name, base, fields, methods):
            if name in ctx:
                raise TypeError(f"the name {name} is already in use for a class or function")
            # is this enough for the class definition -> constructor context?
            fieldnames = []
            for fieldname, _ in fields:
                if fieldname in fieldnames:
                    raise NameError(f"multiple use of {fieldname} for name of field in class {name}")
                fieldnames.append(fieldname)
            # type check method definitions
            methodnames = []
            for method in methods:
                if method.name in methodnames:
                    raise NameError(f"multiple use of {method.name} for name of method in class {name}")
                match method.params[0]:
                    case (Id("self"), TClass(Id(iname), _, _, _)):
                        class_name = name.name
                        if iname != class_name:
                            raise NameError(f"type not accertainable: {iname}, {name}")
                        pass
                    case _:
                        raise TypeError(f"first argument of method {method.name} is not self")     
                # TODO: type check methods
                methodnames.append(method.name)
            methods_types = [(method.name, TCallable(IList([a[1] for a in method.params]), method.ret_ty)) for method in methods]
            class_type = TClass(name, base, fields, IList(methods_types))
            ctx[name] = class_type
            # go over all methods again and annotate the selfs
            for method in methods:
                method.params[0][1].fields = class_type.fields
                method.params[0][1].methods = class_type.methods
                for stmt in method.body:
                    type_annotate_method_stmt(stmt, class_type)
                type_check_def(ctx, method)
            # return value should only be True if we return from a method or statement
            return False

# these have the job to annotate the TClass to all occurances of self in methods
def type_annotate_method_stmt(stmt: Stmt, class_type: TClass):
    match stmt:
        case SExpr(expr):
            type_annotate_method_expr(expr, class_type)
        case SPrint(expr):
            type_annotate_method_expr(expr, class_type)
        case SAssign(lhs, _, rhs):
            match lhs:
                case EField(_):
                    type_annotate_method_expr(lhs, class_type)
            type_annotate_method_expr(rhs, class_type)
        case SIf(test, body, orelse):
            type_annotate_method_expr(test, class_type)
            for s in body:
                type_annotate_method_stmt(s, class_type)
            for o in orelse:
                type_annotate_method_stmt(o, class_type)
        case SWhile(test, body):
            for s in body:
                type_annotate_method_stmt(s, class_type)
            type_annotate_method_expr(test, class_type)
        case SReturn(expr):
            type_annotate_method_expr(expr, class_type)
        case SRaise(expr):
            type_annotate_method_expr(expr, class_type)
        case STry(stry, _, sexcept):
            for s in stry:
                type_annotate_method_stmt(s, class_type)
            for s in sexcept:
                type_annotate_method_stmt(s, class_type)

def type_annotate_method_expr(e: Expr, class_type: TClass):
    match e:
        case EVar(Id("self")):
            e.type = class_type
            return
        case EConst(_):
            return
        case EOp1(_, expr):
            type_annotate_method_expr(expr, class_type)
        case EOp2(left, _, right):
            type_annotate_method_expr(left, class_type)
            type_annotate_method_expr(right, class_type)
        case EIf(test, body, orelse):
            type_annotate_method_expr(test, class_type)
            type_annotate_method_expr(body, class_type)
            type_annotate_method_expr(orelse, class_type)
        case ETuple(exprs):
            for expr in exprs:
                type_annotate_method_expr(expr, class_type)
        case ETupleAccess(expr, _):
            type_annotate_method_expr(expr, class_type)
        case ETupleLen(expr):
            type_annotate_method_expr(expr, class_type)
        case ECall(fun, args):
            type_annotate_method_expr(fun, class_type)
            for expr in args:
                type_annotate_method_expr(expr, class_type)
        case ELambda(_, expr):
            type_annotate_method_expr(expr, class_type)
        case EField(expr, _):
            e.type = class_type
            type_annotate_method_expr(expr, class_type)
        case EMethod(expr, _, args):
            e.type = class_type
            type_annotate_method_expr(expr, class_type)
            for expr in args:
                type_annotate_method_expr(expr, class_type)


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
                case TClass(name, _, fields, _):
                    if len(es) != len(fields):
                        raise TypeError(f"Constructor of Class {name} called with wrong number of arguments")
                    field_tys = [attr[1] for attr in fields]
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
            match exprtype:
                case TClass(classtype, _, fields, _):
                    for (name, fieldtype) in fields:
                        if name == fieldname:
                            return fieldtype
                    raise NameError(f"Cannot find a field with the name {fieldname} in class {classtype}")
                case t:
                    raise TypeError(f"Cannot access field of non-class type {t}")
        # TODO: check if this is complete (method enforcement)
        case EMethod(expr, name, args):
            exprtype = type_check_expr(ctx, expr)
            match exprtype:
                case TClass(classname, base, fields, methods):
                    if len(methods) == 0:
                        raise TypeError(f"could not find any methods associated with {classname}")
                    e.type = exprtype
                    for mname, mtype in methods:
                        if mname == name:
                            m_arg_types = mtype.param_tys[1:]
                            if len(args) != len(m_arg_types):
                                raise TypeError(f"{classname}.{name} expected {len(m_arg_types)} arguments but got {len(args)}")
                            # check argument types
                            for i, arg in enumerate(args):
                                arg_ty = type_check_expr(ctx, arg)
                                if arg_ty != m_arg_types[i]:
                                    raise TypeError(f"expected type {m_arg_types[i]} but got type {arg_ty} in method {classname}.{name}")
                            return mtype.ret_ty
                    else:
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


# Type Equality
# here we check for tansitive subtyping
def check_type_equal(thave: Type, texpect: Type, es: Expr | Stmt):
    match (thave, texpect):
        case (TClass(_, _, _, _), TClass(_, _, _, _)):
            want = texpect
            have = thave
            while have is not None:
                if want == have:
                    return
                have = have.super
            raise TypeError(f"class mismatch: {repr(thave)} seems to not be a subclass of {repr(texpect)} in {repr(es)}")
        case _:
            if thave != texpect:
                raise TypeError(f"I got {repr(thave)} but I expected {repr(texpect)} in {repr(es)}")

def check_ctx_equal(ctx1: TCtx, ctx2: TCtx, es: Expr | Stmt):
    for x in ctx1:
        if x in ctx2:
            check_type_equal(ctx1[x], ctx2[x], es)
        else:
            del ctx1[x]
