from dataclasses import dataclass
# from re import TEMPLATE as T
from types import NoneType
from typing import Literal, cast, Optional

from identifier import Id
from types_ import *
from util.immutable_list import IList

# Unary Operators

type Op1 = Literal["-", "not"]

# Binary Operators

type Op2 = Literal["+", "-", "==", "!=", "<=", "<", ">", ">=", "and", "or", "is"]

# Expressions

type Expr = EConst | EVar | EOp1 | EOp2 | EInput | EIf \
          | ETuple | ETupleAccess | ETupleLen \
          | ECall | ELambda | EField

@dataclass(frozen=True)
class EConst:
    value: int | bool | NoneType

@dataclass
class EVar:
    name: Id

@dataclass(frozen=True)
class EOp1:
    op: Op1
    operand: Expr

@dataclass(frozen=True)
class EOp2:
    left: Expr
    op: Op2
    right: Expr

@dataclass(frozen=True)
class EInput:
    pass

@dataclass(frozen=True)
class EIf:
    test: Expr
    body: Expr
    orelse: Expr

@dataclass(frozen=True)
class ETuple:
    es: IList[Expr]

@dataclass(frozen=True)
class ETupleAccess:
    e: Expr
    index: int

@dataclass(frozen=True)
class ETupleLen:
    e: Expr

@dataclass(frozen=True)
class ECall:
    fun: Expr
    args: IList[Expr]

@dataclass(frozen=True)
class ELambda:
    params: IList[Id]
    body: Expr

@dataclass # not frozen, as we add the type of e to it in the typechecker!
class EField:
    e: Expr
    name: Id

@dataclass
class EMethod:
    e: Expr
    name: Id
    args: IList[Expr]

# Statements

type Stmt = SExpr | SPrint | SAssign | SIf | SWhile | SReturn | SRaise | STry | SClass

@dataclass(frozen=True)
class SExpr:
    expr: Expr

@dataclass(frozen=True)
class SPrint:
    expr: Expr

@dataclass(frozen=True)
class SAssign:
    lhs: Id | EField
    ty: Optional[Type]
    rhs: Expr

@dataclass(frozen=True)
class SIf:
    test: Expr
    body: IList[Stmt]
    orelse: IList[Stmt]

@dataclass(frozen=True)
class SWhile:
    test: Expr
    body: IList[Stmt]

@dataclass(frozen=True)
class SReturn:
    e: Expr

@dataclass(frozen=True)
class SRaise:
    e: Expr

@dataclass(frozen=True)
class STry:
    e_try: IList[Stmt]
    e_var: Id
    e_except: IList[Stmt]

# Declarations

type Decl = DFun

# Function Definition
@dataclass(frozen=True)
class DFun:
    name: Id
    params: IList[tuple[Id, Type]]
    ret_ty: Type
    body: IList[Stmt]

# Class statement

@dataclass(frozen=True)
class SClass:
    name: Id
    super: Optional[Type]
    fields: IList[tuple[Id, Type]]
    methods: IList[DFun]

# Programs

@dataclass
class Program:
    classes: IList[SClass]
    decls: IList[Decl]
    main_body: IList[Stmt]

# Pretty Printing

def indent(s: str) -> str:
    return "\n".join(4 * " " + l for l in s.splitlines())

def pretty(p: Program) -> str:
    return f"{p}\n\n" + pretty_stmts(p.classes) + "\n\n".join(pretty_decl(d) for d in p.decls) + "\n\n" + pretty_stmts(p.main_body)

def pretty_decl(d: Decl) -> str:
    match d:
        case DFun(name, params, ret_ty, body):
            params_str = ", ".join(f"{x}: {pretty_type(t)}" for (x, t) in params)
            return f"def {name}({params_str}) -> {pretty_type(ret_ty)}:\n" + \
                   indent(pretty_stmts(body))

def pretty_stmts(ss: IList[Stmt]) -> str:
    return "\n".join(pretty_stmt(s) for s in ss)

def pretty_stmt(s: Stmt) -> str:
    match s:
        case SExpr(e):
            return pretty_expr(e)
        case SAssign(x, t, e):
            match x: 
                case Id(_):
                    if t is None:
                        return f"{x} = {pretty_expr(e)}"
                    else:
                        return f"{x}: {pretty_type(t)} = {pretty_expr(e)}"
                case EField(_):
                    if t is None:
                        return f"{pretty_expr(x)} = {pretty_expr(e)}"
                    else:
                        return f"{pretty_expr(x)}: {pretty_type(t)} = {pretty_expr(e)}"
                    
        case SPrint(e):
            return "print(" + pretty_expr(e) + ")"
        case SIf(test, body, orelse):
            return f"if {pretty_expr(test)}:\n" \
                   f"{indent(pretty_stmts(body))}\n" \
                   f"else:\n" \
                   f"{indent(pretty_stmts(orelse))}"
        case SWhile(test, body):
            return f"while {pretty_expr(test)}:\n{indent(pretty_stmts(body))}"
        case SReturn(e):
            return f"return {pretty_expr(e)}"
        case SRaise(e):
            return f"raise {pretty_expr(e)}"
        case STry(body, x, s_except):
            return  f"try:\n" \
                    f"{indent(pretty_stmts(body))}\n" \
                    f"except {x}:\n" \
                    f"{indent(pretty_stmts(s_except))}"
        case SClass(name, base, fields, methods):
            field_str = "\n".join(f"{x}: {pretty_type(t)}" for (x, t) in fields)
            basestr = ""
            match base:
                case TClass(bname, _, _, _):
                    basestr = "(" + bname.name + ")"
            return f"{name}{basestr}:\n{indent(field_str)}\n\n" + indent("\n\n".join(pretty_decl(m) for m in methods)) + "\n"

def pretty_expr(e: Expr) -> str:
    match e:
        case EConst(x) | EVar(x):
            return str(x)
        case EOp1(op, e):
            return f"{op} {pretty_expr(e)}"
        case EOp2(e1, op, e2):
            return f"({pretty_expr(e1)} {op} {pretty_expr(e2)})"
        case EInput():
            return "input_int()"
        case EIf(test, body, orelse):
            return f"({pretty_expr(body)} if {pretty_expr(test)} else {pretty_expr(orelse)})"
        case ETuple(entries):
            return "(" + ", ".join(pretty_expr(e) for e in entries) + ")"
        case ETupleAccess(e, i):
            return f"{pretty_expr(e)}[{i}]"
        case ETupleLen(e):
            return f"len({pretty_expr(e)})"
        case ECall(func, args):
            args_str = ", ".join(pretty_expr(e) for e in args)
            return f"{pretty_expr(func)}({args_str})"
        case ELambda(params, body):
            params_str = ", ".join(str(x) for x in params)
            body_str = pretty_expr(body)
            return f"lambda {params_str}: {body_str}"
        case EField(e, name):
            return f"{pretty_expr(e)}.{name}"
        case EMethod(e, name, args):
            return f"{pretty_expr(e)}.{name}(" + ", ".join(pretty_expr(a) for a in args) + ")"

def pretty_anything(x: Program | Decl | Stmt | Expr) -> str:
    try:
        y = pretty(cast(Program, x))
        if y is None:
            raise Exception("not it")
        return y
    except:
        pass

    try:
        y = pretty_decl(cast(Decl, x))
        if y is None:
            raise Exception("not it")
        return y
    except:
        pass

    try:
        y = pretty_stmt(cast(Stmt, x))
        if y is None:
            raise Exception("not it")
        return y
    except:
        pass

    return pretty_expr(cast(Expr, x))
