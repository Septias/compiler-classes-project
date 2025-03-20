from typing import cast

import ast_6_alloc as src
import ast_7_mon as tgt
from identifier import Id
from util.immutable_list import IList, ilist

def monadic(p: src.Program) -> tgt.Program:
    return IList([monadic_decl(d) for d in p])

def monadic_decl(d: src.Decl) -> tgt.Decl:
    match d:
        case src.DFun(name, params, body):
            return tgt.DFun(name, params, monadic_stmts(body))

def monadic_stmts(ss: IList[src.Stmt]) -> IList[tgt.Stmt]:
    out = ilist()
    for s in ss:
        out += monadic_stmt(s)
    return out

def monadic_stmt(s: src.Stmt) -> IList[tgt.Stmt]:
    match s:
        case src.SExpr(e):
            p_e, e_out = monadic_atom(e)
            return p_e
        case src.SPrint(e):
            p_e, e_out = monadic_atom(e)
            return p_e + ilist(tgt.SPrint(e_out))
        case src.SAssign(l, e):
            p_l, l_out = monadic_lhs(l)
            p_e, e_out = monadic_expr(e)
            return p_l + p_e + ilist(tgt.SAssign(l_out, e_out))
        case src.SIf(e, b1, b2):
            p_e, e_out = monadic_condition(e)
            p1 = monadic_stmts(b1)
            p2 = monadic_stmts(b2)
            return p_e + ilist(tgt.SIf(e_out, p1, p2))
        case src.SWhile(e, b):
            test_body, test_expr = monadic_condition(e)
            loop_body = monadic_stmts(b)
            return ilist(tgt.SWhile(test_body, test_expr, loop_body))
        case src.SCollect(n):
            return ilist(tgt.SCollect(n))
        case src.SReturn(e):
            p_e, e_out = monadic_expr(e)
            return p_e + ilist(tgt.SReturn(e_out))
        case src.SRaise(e):
            p_e, e_out = monadic_atom(e)
            return p_e + ilist(tgt.SRaise(e_out))
        case src.STry(body, x, handler):
            pbody = monadic_stmts(body)
            phandler = monadic_stmts(handler)
            return ilist(tgt.STry(pbody, x, phandler))

def monadic_lhs(l: src.Lhs) -> tuple[IList[tgt.Stmt], tgt.Lhs]:
    match l:
        case src.LId(x):
            return ilist(), tgt.LId(x)
        case src.LSubscript(e, i):
            p, e_out = monadic_atom(e)
            return p, tgt.LSubscript(e_out, i)

def monadic_atom(e: src.Expr) -> tuple[IList[tgt.Stmt], tgt.ExprAtom]:
    p, e_out = monadic_expr(e)
    match e_out:
        case tgt.EVar(_) | tgt.EConst(_, _):
            return p, e_out
        case _:
            x = Id.fresh("x")
            return p + ilist(tgt.SAssign(tgt.LId(x), e_out)), tgt.EVar(x)

def monadic_expr(e: src.Expr) -> tuple[IList[tgt.Stmt], tgt.Expr]:
    match e:
        case src.EConst(c, size):
            return ilist(), tgt.EConst(c, size)
        case src.EVar(x):
            return ilist(), tgt.EVar(x)
        case src.EOp1(op, e):
            p_e, e_out = monadic_atom(e)
            return p_e, tgt.EOp1(op, e_out)
        case src.EInput():
            return ilist(), tgt.EInput()
        case src.EOp2(e1, op, e2):
            p_e1, e1_out = monadic_atom(e1)
            p_e2, e2_out = monadic_atom(e2)
            match op:
                case "+" | "-":
                    e_out = tgt.EOp2Arith(e1_out, op, e2_out)
                case "==" | "!=" | "<=" | "<" | ">" | ">=":
                    e_out = tgt.EOp2Comp(e1_out, op, e2_out)
            return p_e1 + p_e2, e_out
        case src.EIf(e1, e2, e3):
            p1, e1 = monadic_condition(e1)
            p2, a2 = monadic_atom(e2)
            p3, a3 = monadic_atom(e3)
            x = Id.fresh("x")
            p = p1 + ilist(
                tgt.SIf(
                    e1,
                    p2 + ilist(tgt.SAssign(tgt.LId(x), a2)),
                    p3 + ilist(tgt.SAssign(tgt.LId(x), a3)),
                )
            )
            return p, tgt.EVar(x)
        case src.EBegin(body, tail):
            p_body = ilist()
            for s in body:
                p_body += monadic_stmt(s)

            p_tail, e_tail = monadic_expr(tail)

            return p_body + p_tail, e_tail
        case src.EGlobal(g):
            return ilist(), tgt.EGlobal(g)
        case src.EAllocate(n):
            return ilist(), tgt.EAllocate(n)
        case src.ETupleAccess(e, i):
            p_e, e_out = monadic_atom(e)
            return p_e, tgt.ETupleAccess(e_out, i)
        case src.ETupleLen(e):
            p_e, e_out = monadic_atom(e)
            return p_e, tgt.ETupleLen(e_out)
        case src.ECall(e_func, e_args):
            p_e_func, e_func_out = monadic_atom(e_func)
            e_args_out: IList[tgt.ExprAtom] = ilist()
            p_args = ilist()
            for e_arg in e_args:
                p_arg, e_arg_out = monadic_atom(e_arg)
                p_args += p_arg
                e_args_out += ilist(e_arg_out)
            return p_e_func + p_args, tgt.ECall(e_func_out, e_args_out)
        case src.EFunRef(name):
            return ilist(), tgt.EFunRef(name)

def monadic_condition(e: src.Expr) -> tuple[IList[tgt.Stmt], tgt.EOp2Comp]:
    match e:
        case src.EOp2(e1, ("==" | "!=" | "<=" | "<" | ">" | ">=") as op, e2):
            b1, x1 = monadic_atom(e1)
            b2, x2 = monadic_atom(e2)
            return (b1 + b2, tgt.EOp2Comp(x1, op, x2))
        case src.EOp1("not", e1):
            b, x = monadic_atom(e1)
            return (b, tgt.EOp2Comp(x, "==", tgt.EConst(0, '64bit')))
        case _:
            b, x = monadic_atom(e)
            return (b, tgt.EOp2Comp(x, "!=", tgt.EConst(0, '64bit')))

