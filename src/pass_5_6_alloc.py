import ast_5_closures as src
import ast_6_alloc as tgt
from identifier import Id
from util.immutable_list import *

def alloc(p: src.Program) -> tgt.Program:
    return IList([alloc_decl(d) for d in p])

def alloc_decl(d: src.Decl) -> tgt.Decl:
    match d:
        case src.DFun(name, params, body):
            return tgt.DFun(name, params, alloc_stmts(body))

def alloc_stmts(ss: IList[src.Stmt]) -> IList[tgt.Stmt]:
    return IList([alloc_stmt(s) for s in ss])

def alloc_stmt(s: src.Stmt) -> tgt.Stmt:
    match s:
        case src.SExpr(e):
            e = alloc_expr(e)
            return tgt.SExpr(e)
        case src.SPrint(e):
            e = alloc_expr(e)
            return tgt.SPrint(e)
        case src.SAssign(x, e):
            lhs = alloc_lhs(x)
            e = alloc_expr(e)
            return tgt.SAssign(lhs, e)
        case src.SIf(e, b1, b2):
            e = alloc_expr(e)
            b1 = alloc_stmts(b1)
            b2 = alloc_stmts(b2)
            return tgt.SIf(e, b1, b2)
        case src.SWhile(e, b):
            e = alloc_expr(e)
            b = alloc_stmts(b)
            return tgt.SWhile(e, b)
        case src.SReturn(e):
            e = alloc_expr(e)
            return tgt.SReturn(e)
        case src.SRaise(e):
            e = alloc_expr(e)
            return tgt.SRaise(e)
        case src.STry(body, x, handler):
            body = alloc_stmts(body)
            handler = alloc_stmts(handler)
            return tgt.STry(body, x, handler)

def alloc_lhs(lhs: src.Lhs) -> tgt.Lhs:
    match lhs:
        case src.LId(x):
            return tgt.LId(x)
        case src.LSubscript(e, i):
            return tgt.LSubscript(alloc_expr(e), i)
        case src.LDictSet(e, key):
            return tgt.LDictSet(alloc_expr(e), alloc_expr(key))

def alloc_expr(e: src.Expr) -> tgt.Expr:
    match e:
        case src.EConst(c, size):
            return tgt.EConst(c, size)
        case src.EVar(x):
            return tgt.EVar(x)
        case src.EInput():
            return tgt.EInput()
        case src.EOp1(op, e1):
            e1 = alloc_expr(e1)
            return tgt.EOp1(op, e1)
        case src.EOp2(e1, op, e2):
            e1 = alloc_expr(e1)
            e2 = alloc_expr(e2)
            return tgt.EOp2(e1, op, e2)
        case src.EIf(e1, e2, e3):
            e1 = alloc_expr(e1)
            e2 = alloc_expr(e2)
            e3 = alloc_expr(e3)
            return tgt.EIf(e1, e2, e3)
        case src.ETuple(es):
            body = ilist()

            # We need 8 bytes for the garbage collector tag and
            # 8 bytes for each element as all our values currently
            # take 8 bytes (boolean, int, tuple pointer).
            num_words = 1 + len(es)
            num_bytes = num_words * 8

            # Translate entry expressions and assign the results to
            # new temporary variables.
            xs = []
            for e in es:
                e_out = alloc_expr(e)
                x = Id.fresh("tup")
                body += ilist(tgt.SAssign(tgt.LId(x), e_out))
                xs += [x]

            # Start a garbage collection if we're out of memory.
            body += ilist(
                tgt.SIf(
                    tgt.EOp2(
                        tgt.EOp2(tgt.EGlobal('gc_free_ptr'), '+', tgt.EConst(num_bytes, '64bit')),
                        '<',
                        tgt.EGlobal('gc_fromspace_end')
                    ),
                    ilist(),
                    ilist(tgt.SCollect(num_words)),
                )
            )

            # Allocate space for the tuple
            v = Id.fresh("v")
            body += ilist(tgt.SAssign(tgt.LId(v), tgt.EAllocate(len(es))))

            # Copy the entry values into the tuple
            for i, x in enumerate(xs):
                body += ilist(tgt.SAssign(tgt.LSubscript(tgt.EVar(v), i), tgt.EVar(x)))

            return tgt.EBegin(body, tgt.EVar(v))
        case src.ETupleAccess(e, i):
            return tgt.ETupleAccess(alloc_expr(e), i)
        case src.ETupleLen(e):
            return tgt.ETupleLen(alloc_expr(e))
        case src.ECall(e_func, e_args):
            return tgt.ECall(alloc_expr(e_func), alloc_exprs(e_args))
        case src.EFunRef(name):
            return tgt.EFunRef(name)
        # BEGIN
        case src.EBegin(ss, e):
            return tgt.EBegin(alloc_stmts(ss), alloc_expr(e))
        # END
        case src.EDict(items):
            return tgt.EDict(IList([(alloc_expr(k), alloc_expr(v)) for k, v in items]))
        case src.EDictAccess(e, key):
            return tgt.EDictAccess(alloc_expr(e), alloc_expr(key))

def alloc_exprs(es: IList[src.Expr]) -> IList[tgt.Expr]:
    return IList([alloc_expr(e) for e in es])

