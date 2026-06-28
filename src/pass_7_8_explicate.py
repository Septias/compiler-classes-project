from typing import Optional

import ast_7_mon as src
import ast_8_exp as tgt
from identifier import Id
from util.immutable_list import IList, ilist
from label import Label

def explicate(p: src.Program) -> tgt.Program:
    return IList([explicate_decl(d) for d in p])

def explicate_decl(d: src.Decl) -> tgt.Decl:
    match d:
        case src.DFun(src.Label(name), params, body):
            l_fun = Label(name)
            l_start = Label(name + "_start")
            l_end = Label(name + "_conclusion")

            out: tgt.Blocks = {}
            out[l_fun] = ilist(tgt.SGoto(l_start))
            out[l_start] = ilist()

            l = explicate_stmts(out, l_start, body, None)

            out[l] += ilist(tgt.SGoto(l_end))
            out[l_end] = ilist()

            return tgt.DFun(tgt.Label(name), params, l_start, l_end, out)

def explicate_stmts(
    out: tgt.Blocks,
    l: Label,
    p: IList[src.Stmt],
    exc_handler: Optional[Label],
) -> Label:
    for s in p:
        l = explicate_stmt(out, l, s, exc_handler)
    return l

def explicate_stmt(
    out: tgt.Blocks,
    l: Label,
    s: src.Stmt,
    exc_handler: Optional[Label],
) -> Label:
    match s:
        case src.SAssign(lhs, e):
            l, lhs_out = explicate_lhs(out, l, lhs)
            l, e_out = explicate_expr(out, l, e)
            out[l] += ilist(tgt.SAssign(lhs_out, e_out))
            match e:
                case src.ECall():
                    return maybe_jump_to_exc_handler(out, l, exc_handler)
                case _:
                    return l
        case src.SPrint(e):
            out[l] += ilist(tgt.SPrint(explicate_atom(e)))
            return l
        case src.SCollect(n):
            out[l] += ilist(tgt.SCollect(n))
            return l
        case src.SIf(src.EOp2Comp(a1, op, a2), b1, b2):
            body_label: Label = Label.fresh("body")
            orelse_label: Label = Label.fresh("orelse")
            cont_label: Label = Label.fresh("cont")

            test = tgt.EOp2Comp(explicate_atom(a1), op, explicate_atom(a2))
            out[l] += ilist(tgt.SIf(test, body_label, orelse_label))

            out[body_label] = ilist()
            out[orelse_label] = ilist()
            body_label_out = explicate_stmts(out, body_label, b1, exc_handler)
            orelse_label_out = explicate_stmts(out, orelse_label, b2, exc_handler)

            out[body_label_out] += ilist(tgt.SGoto(cont_label))
            out[orelse_label_out] += ilist(tgt.SGoto(cont_label))

            out[cont_label] = ilist()
            return cont_label
        case src.SWhile(test_prelude, src.EOp2Comp(a1, op, a2), b):
            test_label: Label = Label.fresh("test")
            body_label: Label = Label.fresh("body")
            cont_label: Label = Label.fresh("cont")

            # Finish current block with goto to `test_label`.
            out[l] += ilist(tgt.SGoto(test_label))

            # Create one (or more) blocks for the condition.
            out[test_label] = ilist()
            test_label_out = explicate_stmts(out, test_label, test_prelude, exc_handler)
            test = tgt.EOp2Comp(explicate_atom(a1), op, explicate_atom(a2))
            out[test_label_out] += ilist(tgt.SIf(test, body_label, cont_label))

            # Create a new block for the body, which should jump
            # to the `test_prelude_label` after running.
            out[body_label] = ilist()
            body_label_out = explicate_stmts(out, body_label, b, exc_handler)
            out[body_label_out] += ilist(tgt.SGoto(test_label))

            # Continue with a new block at `cont_label`
            out[cont_label] = ilist()
            return cont_label
        case src.SReturn(e):
            l, e_out = explicate_expr(out, l, e)
            match e_out:
                case tgt.ECall(e_func, e_args):
                    out[l] += ilist(tgt.STailCall(e_func, e_args))
                case _:
                    x = Id.fresh("x")
                    out[l] += ilist(
                        tgt.SAssign(tgt.LId(x), e_out),
                        tgt.SReturn(tgt.EVar(x)),
                    )
            return l
        case src.STry(try_block, x, exc_block):
            # Create a new label for the exception handler
            new_exc_handler = Label.fresh("exc_handler")

            # Create identifiers for the stack variables in which
            # the select pass stores the previous exc handler information.
            saved_exc = tgt.ExcTmpNames(
                Id.fresh("saved_exc_sp"),
                Id.fresh("saved_exc_fp"),
                Id.fresh("saved_exc_handler"),
            )

            # Explicate the try statements into the current basic block
            out[l] += ilist(tgt.STryEnter(new_exc_handler, saved_exc)) 
            l = explicate_stmts(out, l, try_block, new_exc_handler)
            out[l] += ilist(tgt.STryExit(saved_exc)) 

            # Explicate the exception handler statements into the new exception handler basic block
            out[new_exc_handler] = ilist(
                tgt.STryExit(saved_exc),
                tgt.SExcEnter(x),
            ) 
            l_handler_cont = explicate_stmts(out, new_exc_handler, exc_block, exc_handler)

            # Create a new label for the code that comes after the try-except-statement.
            # After finishing the try block without exception or after finishing the exception handler,
            # we need to jump to this label to continue.
            l_cont = Label.fresh("after_try")
            out[l_handler_cont] += ilist(tgt.SGoto(l_cont))
            out[l] += ilist(tgt.SGoto(l_cont))
            out[l_cont] = ilist()
            return l_cont
        case src.SRaise(e):
            e_out = explicate_atom(e)
            out[l] += ilist(tgt.SRaise(e_out))
            return maybe_jump_to_exc_handler(out, l, exc_handler)

def maybe_jump_to_exc_handler(
    out: tgt.Blocks,
    l: Label,
    exc_handler: Optional[Label],
) -> Label:
    if exc_handler is None:
        return l
    else:
        l_cont = Label.fresh("try_cont")
        out[l] += ilist(tgt.SIf(
            tgt.EOp2Comp(
                tgt.EConst(0, '64bit'),
                '!=',
                tgt.EConst(0, '64bit'),
            ),
            exc_handler,
            l_cont,
        ))
        out[l_cont] = ilist()
        return l_cont

def explicate_lhs(
    out: tgt.Blocks,
    l: Label,
    lhs: src.Lhs
) -> tuple[Label, tgt.Lhs]:
    match lhs:
        case src.LId(x):
            return l, tgt.LId(x)
        case src.LSubscript(e, i):
            return l, tgt.LSubscript(explicate_atom(e), i)
        case src.LDictSet(e, key):
            return l, tgt.LDictSet(explicate_atom(e), explicate_atom(key))

def explicate_expr(
    out: tgt.Blocks,
    l: Label,
    e: src.Expr
) -> tuple[Label, tgt.Expr]:
    match e:
        case src.EVar(_) | src.EConst(_):
            return l, explicate_atom(e)
        case src.EInput():
            return l, tgt.EInput()
        case src.EOp1(op, a):
            e_out = explicate_atom(a)
            return l, tgt.EOp1(op, e_out)
        case src.EOp2Arith(a1, op, a2):
            a1_out = explicate_atom(a1)
            a2_out = explicate_atom(a2)
            return l, tgt.EOp2Arith(a1_out, op, a2_out)
        case src.EOp2Comp(a1, op, a2):
            a1_out = explicate_atom(a1)
            a2_out = explicate_atom(a2)
            return l, tgt.EOp2Comp(a1_out, op, a2_out)
        case src.EGlobal(x):
            return l, tgt.EGlobal(x)
        case src.EAllocate(n):
            return l, tgt.EAllocate(n)
        case src.ETupleLen(e1):
            e1_out = explicate_atom(e1)
            return l, tgt.ETupleLen(e1_out)
        case src.ETupleAccess(e1, i):
            e1_out = explicate_atom(e1)
            return l, tgt.ETupleAccess(e1_out, i)
        case src.ECall(e_func, e_args):
            e_func_out = explicate_atom(e_func)
            e_args_out = explicate_atoms(e_args)
            return l, tgt.ECall(e_func_out, e_args_out)
        case src.EFunRef(name):
            return l, tgt.EFunRef(name)
        case src.EDict(items):
            items_out = IList([(explicate_atom(k), explicate_atom(v)) for k, v in items])
            return l, tgt.EDict(items_out)
        case src.EDictAccess(e, key):
            return l, tgt.EDictAccess(explicate_atom(e), explicate_atom(key))

def explicate_atoms(
    es: IList[src.ExprAtom],
) -> IList[tgt.ExprAtom]:
    return IList([explicate_atom(e) for e in es])

def explicate_atom(
    a: src.ExprAtom
) -> tgt.ExprAtom:
    match a:
        case src.EVar(x):
            return tgt.EVar(x)
        case src.EConst(x, size):
            return tgt.EConst(x, size)

