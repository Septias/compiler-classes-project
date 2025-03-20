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
                case TCallable(arg_tys, res_ty):
                    if len(es) != len(arg_tys):
                        raise TypeError(f"Calling function with wrong number of arguments {e}")
                    for (e, ty) in zip(es, arg_tys):
                        check_expr(ctx, e, ty)
                    return res_ty
                case t:
                    raise TypeError(f"Calling non-function type {t}")
        case ELambda():
            raise TypeError(f"Cannot synthesize type of {pretty_expr(e)}")
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

def check_type_equal(thave: Type, texpect: Type, es: Expr | Stmt):
    if thave != texpect:
        raise TypeError(f"I got {repr(thave)} but I expected {repr(texpect)} in {repr(es)}")

def check_ctx_equal(ctx1: TCtx, ctx2: TCtx, es: Expr | Stmt):
    for x in ctx1:
        if x in ctx2:
            check_type_equal(ctx1[x], ctx2[x], es)
        else:
            del ctx1[x]
