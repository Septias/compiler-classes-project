import ast_1_python as src
import ast_2_shrunk as tgt
from types_ import *
from identifier import *
from util.immutable_list import *

def shrink(p: src.Program) -> tgt.Program:
    # convert the class and method definitions
    class_funs = shrink_classes(p.classes)
    new_decls = IList([shrink_decl(d) for d in p.decls])
    # Add the top-level statements to a function called `program_main`
    program_main_body = shrink_stmts(p.main_body)
    program_main = tgt.DFun(tgt.Id("program_main"), ilist(), program_main_body)
    new_decls = new_decls + class_funs
    # Create the real main function which calls the `program_main` in a try-block
    # to report exceptions which otherwise would be unhandled.
    exc_id = Id.fresh("x")
    main_body = ilist(tgt.STry(
        ilist(
            tgt.SExpr(tgt.ECall(tgt.EVar(Id("program_main")), ilist()))
        ),
        exc_id,
        ilist(
            tgt.SPrint(tgt.EVar(exc_id))
        ),
    ))
    main = tgt.DFun(tgt.Id("main"), ilist(), main_body)

    return new_decls + ilist(program_main, main)

def shrink_decl(d: src.Decl) -> tgt.Decl:
    match d:
        case src.DFun(name, params, _, body):
            params = IList([x for (x, _) in params])
            return tgt.DFun(name, params, shrink_stmts(body))

def shrink_stmts(ss: IList[src.Stmt]) -> IList[tgt.Stmt]:
    return IList([shrink_stmt(s) for s in ss])

def shrink_classes(cc: IList[src.SClass]) -> IList[tgt.DFun]:
    all_funs = []
    for c in cc:
        all_funs.extend(shrink_class(c))
    return IList(all_funs)

# gets a TClass and returns a list of unique method names
def method_override_resolution(t: TClass) -> IList[Id]:
    res = []
    match t:
        case TClass(_, base, _, methods):
            res = [m[0] for m in methods]
            while base is not None:
                match base:
                    case TClass(_, new_base, _, new_methods):
                        for nm, _ in new_methods:
                            if nm in res:
                                continue
                            res = [nm] + res
                        base = new_base
                    case _:
                        base = None
        case _:
            raise TypeError(f"tried to find class method structure of illegal type {t}")
    return IList(res)

def shrink_class(c: src.SClass) -> list[tgt.DFun]:
    class_constructors = []
    class_methods = []
    match c:
        case src.SClass(name, base, fields, methods):
            closures = []
            methods_types = [(method.name, TCallable(IList([a[1] for a in method.params]), method.ret_ty)) for method in methods]
            class_type = TClass(name, base, fields, IList(methods_types))
            unique_method_names = method_override_resolution(class_type)
            for method in methods:
                shrunk = shrink_decl(method)
                method_to_fun_name = name.name + "$" + shrunk.name.name
                shrunken = tgt.DFun(Id(method_to_fun_name), shrunk.params, shrunk.body)
                class_methods.append(shrunken)
            for method_name in unique_method_names:
                # search in which class method_name was last overridden and insert closure 
                current = class_type
                while current is not None:
                    match current:
                        case TClass(current_name, current_base, _, current_methods):
                            if method_name in [cm[0] for cm in current_methods]:
                                closures.append(tgt.EVar(Id(current_name.name + "$" + method_name.name)))
                                break
                            current = current_base
                        case _:
                            current = None
            class_obj = tgt.ETuple(IList(closures))
            ids = []
            while base is not None:
                match base:
                    case TClass(_, new_super, super_fields, _):
                        # new ids in front as we go from child to parent class
                        ids = [super_field[0] for super_field in super_fields] + ids
                        base = new_super
                    case TBool() | TInt():
                        base = None
                    case _:
                        raise TypeError(f"{name} has illegal super {super}")
            # we have built all parent fields, add fields of current (child) class at the end
            ids = ids + [field[0] for field in fields]
            constructor_body = ilist(tgt.SReturn(tgt.ETuple(IList([class_obj] + [tgt.EVar(id) for id in ids]))))
            constructor = tgt.DFun(name, IList(ids), constructor_body)
            class_constructors.append(constructor)
            return class_constructors + class_methods
        case _:
            raise Exception(f"internal error: non-class {c} found during shrinking of class defs")

def shrink_stmt(s: src.Stmt) -> tgt.Stmt:
    match s:
        case src.SExpr(e):
            e = shrink_expr(e)
            return tgt.SExpr(e)
        case src.SPrint(e):
            e = shrink_expr(e)
            return tgt.SPrint(e)
        # BEGIN
        case src.SAssign(x, _, e):
        # END
            e = shrink_expr(e)
            match x:
                case Id(_):
                    return tgt.SAssign(x, e)
                case src.EField(expr, name):
                    # TODO: we need to assign/override the value inside the tuple with a new one
                    # how: we already have a way to write inside a tuple when it is being allocated (pass_5_6)
                    # idea: have subscript assignments (e.g. x[5] = 1), as they functionally do the same thing.
                    # it boils down to: find heap memory address and write into it.
                    # we already have subscript assignment in pass 3_4 to deal with assignment conversion in regards to lambdas with free variables
                    # idea: convert this SAssign with efield on the lhs to a form compatible with LSubscript (needs expr and offset)
                    # we can get the offset by counting at which point in the tuple the field is located
                    # ALSO: this can occur in multiple places: 
                    # 1: inside a method - self is set to the first argument (is that enough?)
                    # 2: outside one - the variable can be processed like any other
                    return tgt.SAssign(shrink_expr(x), e)
        case src.SIf(e, b1, b2):
            e = shrink_expr(e)
            b1 = shrink_stmts(b1)
            b2 = shrink_stmts(b2)
            return tgt.SIf(e, b1, b2)
        case src.SWhile(e, b):
            e = shrink_expr(e)
            b = shrink_stmts(b)
            return tgt.SWhile(e, b)
        case src.SReturn(e):
            e = shrink_expr(e)
            return tgt.SReturn(e)
        case src.SRaise(e):
            e = shrink_expr(e)
            return tgt.SRaise(e)
        case src.STry(body, x, handler):
            body = shrink_stmts(body)
            handler = shrink_stmts(handler)
            return tgt.STry(body, x, handler)
        # class statements should not occur here as they are treated completley seperatley
        case src.SClass(name, _, _, _):
            raise Exception(f"Internal error: encountered class definition of {name} in body.")


def shrink_expr(e: src.Expr) -> tgt.Expr:
    match e:
        case src.EConst(c):
            return tgt.EConst(c, '63bit')
        case src.EVar(x):
            return tgt.EVar(x)
        case src.EInput():
            return tgt.EInput()
        case src.EOp1(op, e1):
            e1 = shrink_expr(e1)
            return tgt.EOp1(op, e1)
        case src.EOp2(e1, op, e2):
            e1 = shrink_expr(e1)
            e2 = shrink_expr(e2)
            match op:
                case "and":
                    return tgt.EIf(e1, e2, tgt.EConst(False, '63bit'))
                case "or":
                    return tgt.EIf(e1, tgt.EConst(True, '63bit'), e2)
                case "is":
                    # As tuples are represented as pointers, the 'is' operator
                    # corresponds simply to equality.
                    return tgt.EOp2(e1, "==", e2)
                case _:
                    return tgt.EOp2(e1, op, e2)
        case src.EIf(e1, e2, e3):
            e1 = shrink_expr(e1)
            e2 = shrink_expr(e2)
            e3 = shrink_expr(e3)
            return tgt.EIf(e1, e2, e3)
        case src.ETuple(es):
            return tgt.ETuple(IList([shrink_expr(e) for e in es]))
        case src.ETupleAccess(e, i):
            return tgt.ETupleAccess(shrink_expr(e), i)
        case src.ETupleLen(e):
            return tgt.ETupleLen(shrink_expr(e))
        case src.ECall(e_fun, e_args):
            e_fun = shrink_expr(e_fun)
            e_args = IList([shrink_expr(arg) for arg in e_args])
            return tgt.ECall(e_fun, e_args)
        # BEGIN
        case src.ELambda(params, body):
            return tgt.ELambda(params, shrink_expr(body))
        # END
        case src.EField(expr, name):
            class_type = e.type # type: ignore
            ids = []
            match class_type:
                case TClass(_, base, _, _):
                    while base is not None:
                        match base:
                            case TClass(_, new_super, super_fields, _):
                                # new ones in front as we go from child to parent class
                                ids = [super_field[0] for super_field in super_fields] + ids
                                base = new_super
                            case TBool() | TInt():
                                base = None
            field_ids = ids + [f[0]for f in class_type.fields]
            if name in field_ids:
                i = 0
                for field_name in field_ids:
                    if field_name == name:
                        break
                    i += 1
                return tgt.ETupleAccess(shrink_expr(expr), i + 1)
            else:
                raise RuntimeError(f"Broken pipeline: field {name} does not exist for {class_type} in {e}")
        case src.EMethod(expr, name, args):
            class_type = e.type # type: ignore
            method_ids = method_override_resolution(class_type)
            if name in method_ids:
                i = 0
                for method_name in method_ids:
                    if method_name == name:
                        break
                    i += 1
                clazz = tgt.ETupleAccess(shrink_expr(expr), 0)
                # this should be an EVar whos name is the name of the method/function
                method = tgt.ETupleAccess(clazz, i)
                # shrink args, add self first:
                new_args = [shrink_expr(expr)]
                for arg in args:
                    new_args.append(shrink_expr(arg))
                return tgt.ECall(method, IList(new_args))
            else:
                raise Exception(f"could not find called method {name}")
