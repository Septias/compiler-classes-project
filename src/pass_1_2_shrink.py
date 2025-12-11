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

# gets a TClass and returns lists of unique field and method names
def unique_member_resolution(t: TClass) -> tuple[IList[Id], IList[Id]]:
    res_methods = []
    res_fields = []
    match t:
        case TClass(_, base, fields, methods):
            res_methods = [m[0] for m in methods]
            res_fields = [n[0] for n in fields]
            while base is not None:
                match base:
                    case TClass(_, new_base, new_fields, new_methods):
                        for nm, _ in new_methods:
                            if nm in res_methods:
                                continue
                            res_methods = [nm] + res_methods
                        for nf, _ in new_fields:
                            res_fields = [nf] + res_fields
                        base = new_base
                    case _:
                        base = None
        case _:
            raise TypeError(f"tried to find class method structure of illegal type {t}")
    return (IList(res_fields), IList(res_methods))

def shrink_class(c: src.SClass) -> list[tgt.DFun]:
    class_constructors = []
    class_methods = []
    match c:
        case src.SClass(name, base, fields, methods):
            closures = []
            methods_types = [(method.name, TCallable(IList([a[1] for a in method.params]), method.ret_ty)) for method in methods]
            class_type = TClass(name, base, fields, IList(methods_types))
            ids, unique_method_names = unique_member_resolution(class_type)
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
                    shrunk = shrink_expr(x)
                    match shrunk:
                        case tgt.ETupleAccess():
                            return tgt.SAssign(shrunk, e)
                        case _:
                            raise Exception(f"can not assign to {expr}")
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
            field_ids, _ = unique_member_resolution(class_type)
            if name in field_ids:
                i = 0
                for field_name in field_ids:
                    if field_name == name:
                        break
                    i += 1
                return tgt.ETupleAccess(shrink_expr(expr), i + 1)
            else:
                raise Exception(f"Broken pipeline: field {name} does not exist for {class_type} in {e}")
        case src.EMethod(expr, name, args):
            # TODO: this can be a call to a member variable of type Callable.
            class_type = e.type # type: ignore
            field_ids, method_ids = unique_member_resolution(class_type)
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
            # we did not find the called object in the methods, so we look in the fields to check if we have a Callable with name here
            elif name in field_ids:
                i = 0
                for field_name in field_ids:
                    if field_name == name:
                        break
                    i += 1
                # here we need to access the member variable in the tuple of the object (NOT the class object) and call the ELambda there
                # (index + 1) as first obj in tuple is class obj
                callable_member = tgt.ETupleAccess(shrink_expr(expr), i + 1)
                new_args = []
                for arg in args:
                    new_args.append(shrink_expr(arg))
                return tgt.ECall(callable_member, IList(new_args))
            # could not find it anywhere - can not generate code
            else:
                raise Exception(f"could not find called method {name}")
