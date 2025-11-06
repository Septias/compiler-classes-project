# The only interesting thing happens in `collect_function_funs` and
# the variable case of `reveal_expr`.

import ast_2_shrunk as src
import ast_3_revealed as tgt
from identifier import Id
from label import Label
from util.immutable_list import *

def reveal(p: src.Program) -> tgt.Program:
    funs = collect_functions(p)
    return IList([reveal_decl(funs, d) for d in p])

def collect_functions(p: src.Program) -> set[Id]:
    funs = set()
    for d in p:
        match d:
            case src.DFun(name, _, _):
                funs.add(name)
    return funs

def reveal_decl(funs: set[Id], d: src.Decl) -> tgt.Decl:
    match d:
        case src.DFun(name, params, body):
            return tgt.DFun(Label(name.name), params, reveal_stmts(funs, body))

def reveal_stmts(funs: set[Id], ss: IList[src.Stmt]) -> IList[tgt.Stmt]:
    return IList([reveal_stmt(funs, s) for s in ss])

def reveal_stmt(funs: set[Id], s: src.Stmt) -> tgt.Stmt:
    match s:
        case src.SExpr(e):
            e = reveal_expr(funs, e)
            return tgt.SExpr(e)
        case src.SPrint(e):
            e = reveal_expr(funs, e)
            return tgt.SPrint(e)
        case src.SAssign(x, e):
            e = reveal_expr(funs, e)
            match x:
                case Id(_):
                    return tgt.SAssign(x, e)
                case src.ETupleAccess(expr, idx):
                    return tgt.SAssign(tgt.ETupleAccess(reveal_expr(funs, expr), idx), e)
        case src.SIf(e, b1, b2):
            e = reveal_expr(funs, e)
            b1 = reveal_stmts(funs, b1)
            b2 = reveal_stmts(funs, b2)
            return tgt.SIf(e, b1, b2)
        case src.SWhile(e, b):
            e = reveal_expr(funs, e)
            b = reveal_stmts(funs, b)
            return tgt.SWhile(e, b)
        case src.SReturn(e):
            e = reveal_expr(funs, e)
            return tgt.SReturn(e)
        case src.SRaise(e):
            e = reveal_expr(funs, e)
            return tgt.SRaise(e)
        case src.STry(body, x, handler):
            body = reveal_stmts(funs, body)
            handler = reveal_stmts(funs, handler)
            return tgt.STry(body, x, handler)



def reveal_expr(funs: set[Id], e: src.Expr) -> tgt.Expr:
    match e:
        case src.EConst(c, size):
            return tgt.EConst(c, size)
        case src.EVar(x):
            if x in funs:
                return tgt.EFunRef(Label(x.name))
            else:
                return tgt.EVar(x)
        case src.EInput():
            return tgt.EInput()
        case src.EOp1(op, e1):
            e1 = reveal_expr(funs, e1)
            return tgt.EOp1(op, e1)
        case src.EOp2(e1, op, e2):
            e1 = reveal_expr(funs, e1)
            e2 = reveal_expr(funs, e2)
            return tgt.EOp2(e1, op, e2)
        case src.EIf(e1, e2, e3):
            e1 = reveal_expr(funs, e1)
            e2 = reveal_expr(funs, e2)
            e3 = reveal_expr(funs, e3)
            return tgt.EIf(e1, e2, e3)
        case src.ETupleAccess(e, i):
            return tgt.ETupleAccess(reveal_expr(funs, e), i)
        case src.ETupleLen(e):
            return tgt.ETupleLen(reveal_expr(funs, e))
        case src.ETuple(es):
            return tgt.ETuple(reveal_exprs(funs, es))
        case src.ECall(e_func, e_args):
            return tgt.ECall(reveal_expr(funs, e_func), reveal_exprs(funs, e_args))
        # BEGIN
        case src.ELambda(params, body):
            return tgt.ELambda(params, reveal_expr(funs, body))
        # END

def reveal_exprs(funs: set[Id], es: IList[src.Expr]) -> IList[tgt.Expr]:
    return IList([reveal_expr(funs, e) for e in es])

