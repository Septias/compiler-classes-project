# The interesting parts happen at function declarations and function calls

import ast_5_closures as src
import ast_5_closures as tgt
from identifier import Id
from types_ import *
from util.immutable_list import *

def limit(p: src.Program) -> tgt.Program:
    return IList([limit_decl(d) for d in p])

def limit_decl(d: src.Decl) -> tgt.Decl:
    match d:
        case src.DFun(name, params, body):
            if len(params) > 8:
                first_params = params[:7]
                rest_params = params[7:]
                rest_param = Id("params:rest")
                params = first_params + ilist(rest_param)
                new_stmts = IList([
                    tgt.SAssign(tgt.LId(x), tgt.ETupleAccess(tgt.EVar(rest_param), i))
                    for (i, x) in enumerate(rest_params)
                ])
                body = new_stmts + body
            return tgt.DFun(name, params, limit_stmts(body))

def limit_stmts(ss: IList[src.Stmt]) -> IList[tgt.Stmt]:
    return IList([limit_stmt(s) for s in ss])

def limit_stmt(s: src.Stmt) -> tgt.Stmt:
    match s:
        case src.SExpr(e):
            e = limit_expr(e)
            return tgt.SExpr(e)
        case src.SPrint(e):
            e = limit_expr(e)
            return tgt.SPrint(e)
        case src.SAssign(lhs, e):
            e = limit_expr(e)
            lhs = limit_lhs(lhs)
            return tgt.SAssign(lhs, e)
        case src.SIf(e, b1, b2):
            e = limit_expr(e)
            b1 = limit_stmts(b1)
            b2 = limit_stmts(b2)
            return tgt.SIf(e, b1, b2)
        case src.SWhile(e, b):
            e = limit_expr(e)
            b = limit_stmts(b)
            return tgt.SWhile(e, b)
        case src.SReturn(e):
            e = limit_expr(e)
            return tgt.SReturn(e)
        case src.SRaise(e):
            e = limit_expr(e)
            return tgt.SRaise(e)
        case src.STry(body, x, handler):
            body = limit_stmts(body)
            handler = limit_stmts(handler)
            return tgt.STry(body, x, handler)

def limit_lhs(lhs: src.Lhs) -> tgt.Lhs:
    match lhs:
        case src.LId(x):
            return tgt.LId(x)
        case src.LSubscript(e, i):
            return tgt.LSubscript(limit_expr(e), i)
        case src.LDictSet(e, key):
            return tgt.LDictSet(limit_expr(e), limit_expr(key))

def limit_expr(e: src.Expr) -> tgt.Expr:
    match e:
        case src.EConst(c, size):
            return tgt.EConst(c, size)
        case src.EVar(x):
            return tgt.EVar(x)
        case src.EInput():
            return tgt.EInput()
        case src.EOp1(op, e1):
            e1 = limit_expr(e1)
            return tgt.EOp1(op, e1)
        case src.EOp2(e1, op, e2):
            e1 = limit_expr(e1)
            e2 = limit_expr(e2)
            return tgt.EOp2(e1, op, e2)
        case src.EIf(e1, e2, e3):
            e1 = limit_expr(e1)
            e2 = limit_expr(e2)
            e3 = limit_expr(e3)
            return tgt.EIf(e1, e2, e3)
        case src.ETuple(es):
            return tgt.ETuple(limit_exprs(es))
        case src.ETupleAccess(e, i):
            return tgt.ETupleAccess(limit_expr(e), i)
        case src.ETupleLen(e):
            return tgt.ETupleLen(limit_expr(e))
        case src.ECall(e_func, e_args):
            if len(e_args) > 8:
                e_args = e_args[:7] + ilist(tgt.ETuple(e_args[7:]))
            return tgt.ECall(limit_expr(e_func), limit_exprs(e_args))
        case src.EFunRef(name):
            return tgt.EFunRef(name)
        # BEGIN
        case src.EBegin(ss, e):
            return tgt.EBegin(limit_stmts(ss), limit_expr(e))
        # END
        case src.EDict(items):
            return tgt.EDict(IList([(limit_expr(k), limit_expr(v)) for k, v in items]))
        case src.EDictAccess(e, key):
            return tgt.EDictAccess(limit_expr(e), limit_expr(key))

def limit_exprs(es: IList[src.Expr]) -> IList[tgt.Expr]:
    return IList([limit_expr(e) for e in es])

