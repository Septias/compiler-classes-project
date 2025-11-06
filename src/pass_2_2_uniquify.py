import ast_2_shrunk as src
import ast_2_shrunk as tgt
from identifier import Id
from util.immutable_list import *

# BEGIN
def uniquify(p: src.Program) -> tgt.Program:
    renaming = {}

    # Keep function names the same
    for d in p:
        match d:
            case src.DFun(name, _, _):
                renaming[name] = name

    return IList([uniquify_decl(renaming.copy(), d) for d in p])

def uniquify_decl(renaming: dict[Id, Id], d: src.Decl) -> tgt.Decl:
    match d:
        case src.DFun(name, params, body):
            new_params = IList([Id.fresh(x.name) for x in params])
            renaming |= { x: x_new for (x, x_new) in zip(params, new_params) }
            return tgt.DFun(name, new_params, uniquify_stmts(renaming, body))

def uniquify_stmts(renaming: dict[Id, Id], ss: IList[src.Stmt]) -> IList[tgt.Stmt]:
    return IList([uniquify_stmt(renaming, s) for s in ss])

def uniquify_stmt(renaming: dict[Id, Id], s: src.Stmt) -> tgt.Stmt:
    match s:
        case src.SExpr(e):
            e = uniquify_expr(renaming, e)
            return tgt.SExpr(e)
        case src.SPrint(e):
            e = uniquify_expr(renaming, e)
            return tgt.SPrint(e)
        case src.SAssign(x, e):
            match x:
                case Id(_):
                    if x in renaming:
                        y = renaming[x]
                    else:
                        y = Id.fresh(x.name)
                        renaming[x] = y
                    e = uniquify_expr(renaming, e)
                    return tgt.SAssign(y, e)
                case src.ETupleAccess(expr, idx):
                    return tgt.SAssign(tgt.ETupleAccess(uniquify_expr(renaming, expr), idx), uniquify_expr(renaming, e))
        case src.SIf(e, b1, b2):
            e = uniquify_expr(renaming, e)
            b1 = uniquify_stmts(renaming, b1)
            b2 = uniquify_stmts(renaming, b2)
            return tgt.SIf(e, b1, b2)
        case src.SWhile(e, b):
            e = uniquify_expr(renaming, e)
            b = uniquify_stmts(renaming, b)
            return tgt.SWhile(e, b)
        case src.SReturn(e):
            e = uniquify_expr(renaming, e)
            return tgt.SReturn(e)
        case src.SRaise(e):
            e = uniquify_expr(renaming, e)
            return tgt.SRaise(e)
        case src.STry(body, x, handler):
            body = uniquify_stmts(renaming, body)
            renaming[x] = Id.fresh(x.name)
            handler = uniquify_stmts(renaming, handler)
            return tgt.STry(body, renaming[x], handler)

def uniquify_expr(renaming: dict[Id, Id], e: src.Expr) -> tgt.Expr:
    match e:
        case src.EConst(c, size):
            return tgt.EConst(c, size)
        case src.EVar(x):
            return tgt.EVar(renaming[x])
        case src.EInput():
            return tgt.EInput()
        case src.EOp1(op, e1):
            e1 = uniquify_expr(renaming, e1)
            return tgt.EOp1(op, e1)
        case src.EOp2(e1, op, e2):
            e1 = uniquify_expr(renaming, e1)
            e2 = uniquify_expr(renaming, e2)
            return tgt.EOp2(e1, op, e2)
        case src.EIf(e1, e2, e3):
            e1 = uniquify_expr(renaming, e1)
            e2 = uniquify_expr(renaming, e2)
            e3 = uniquify_expr(renaming, e3)
            return tgt.EIf(e1, e2, e3)
        case src.ETupleAccess(e, i):
            return tgt.ETupleAccess(uniquify_expr(renaming, e), i)
        case src.ETupleLen(e):
            return tgt.ETupleLen(uniquify_expr(renaming, e))
        case src.ETuple(es):
            return tgt.ETuple(uniquify_exprs(renaming, es))
        case src.ECall(e_func, e_args):
            return tgt.ECall(uniquify_expr(renaming, e_func), uniquify_exprs(renaming, e_args))
        case src.ELambda(params, body):
            # Always use new names for the parameters in a lambda,
            # as they shadow variables with the same name from the outside.
            renaming = renaming.copy()
            new_params = ilist()
            for p in params:
                p_new = Id.fresh(p.name)
                renaming[p] = p_new
                new_params += ilist(p_new)
            return tgt.ELambda(new_params, uniquify_expr(renaming, body))

def uniquify_exprs(renaming: dict[Id, Id], es: IList[src.Expr]) -> IList[tgt.Expr]:
    return IList([uniquify_expr(renaming, e) for e in es])
# END
