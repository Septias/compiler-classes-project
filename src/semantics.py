from ast import expr
from dataclasses import dataclass
from optparse import Option
# from re import TEMPLATE as T
from typing import Optional
from types import NoneType
from collections import Counter

from ast_1_python import *
from util.immutable_list import IList, ilist

# Simulate Integer Overflow Behavior

MAX_INT_63 = 2**62 - 1
MIN_INT_63 = -(2**62)

def simulate_over_and_underflow(i: int) -> int:
    while i > MAX_INT_63:
        i = i - (2**63)
    while i < MIN_INT_63:
        i = i + (2**63)
    return i

# Values

type Value = int | bool | NoneType | VTuple | VFunction | VClass | VObject

# Value Environment

@dataclass(frozen=True)
class RTEnv:
    current: dict[Id, Value]
    parent: Optional['RTEnv']

def lookup(cur: Optional[RTEnv], x: Id) -> Value:
    while cur is not None and x not in cur.current.keys():
        cur = cur.parent
    if cur is None:
        raise Exception(f"Identifier not found {x}")
    else:
        return cur.current[x]

def assign(env: RTEnv, x: Id, v: Value):
    env.current[x] = v

@dataclass
class VTuple:
    entries: list[Value]

@dataclass
class VFunction:
    name: Id
    xs: IList[Id]
    body: IList[Stmt]
    env: RTEnv

@dataclass
class UserException(Exception):
    value: Value

@dataclass(frozen=True)
class VClass:
    name: Id
    super: Optional[Type]
    fieldnames: IList[Id]
    methods: IList[Value]

@dataclass
class VObject:
    classref: VClass
    fields: dict[Id, Value]

# Evaluation

def apply_fun(f: Value, xs: tuple[Value, ...]) -> Optional[Value]:
    match f:
        case VFunction(_, parms, body, env):
            fenv = RTEnv(dict(zip(parms, xs)), env)
            return eval_stmts(fenv, body)
        case VClass(_, super, fieldnames, _):
            while super is not None:
                match super:
                    case TClass(_, super_super, super_fieldnames, _):
                        fieldnames = IList([superfield[0] for superfield in super_fieldnames]) + fieldnames
                        super = super_super
                    case TBool() | TInt():
                        super = None
                    case _:
                        raise TypeError(f"impossible parent type found at runtime: {super}")
            counts = Counter(fieldnames)
            duplicate_elements = [ item for item, count in counts.items() if count > 1]
            if len(duplicate_elements) > 0:
                raise Exception(f"Multiple use of member names: {duplicate_elements}")
            if len(xs) != len(fieldnames):
                raise Exception(f"Class expected {len(fieldnames)} arguments for construction but got {len(xs)}")
            res = {}
            for field, val in zip(fieldnames, xs):
                res[field] = val
            return VObject(f, res)
        case _:
            raise Exception('apply_fun: unexpected value ' + repr(f))

def eval_expr(env: RTEnv, e: Expr) -> Value:
    match e:
        case EConst(c):
            return c
        case EVar(x):
            return lookup(env, x)
        case EOp1(op, e):
            v = eval_expr(env, e)
            match v:
                case VTuple(_) | VFunction() | VClass() | VObject() | None:
                    raise Exception(f"Unary operator '{op}' not allowed for '{pretty_expr(e)}'")
                case _:
                    match op:
                        case "-":
                            return -v
                        case "not":
                            return not v
        case EOp2(e1, "and", e2):
            v1 = eval_expr(env, e1)
            if v1:
                return eval_expr(env, e2)
            return False
        case EOp2(e1, "or", e2):
            v1 = eval_expr(env, e1)
            if not v1:
                return eval_expr(env, e2)
            return True
        case EOp2(e1, op, e2):
            v1 = eval_expr(env, e1)
            v2 = eval_expr(env, e2)
            match v1, v2:
                case (int(x1) | bool(x1)), (int(x2) | bool(x2)):
                    match op:
                        case "+":
                            return simulate_over_and_underflow(x1 + x2)
                        case "-":
                            return simulate_over_and_underflow(x1 - x2)
                        case "==":
                            return x1 == x2
                        case "!=":
                            return x1 != x2
                        case "<=":
                            return x1 <= x2
                        case "<":
                            return x1 < x2
                        case ">":
                            return x1 > x2
                        case ">=":
                            return x1 >= x2
                        case _:
                            raise Exception("Impossible!")
                case VTuple(_), VTuple(_):
                    match op:
                        case "is":
                            return v1 == v2
                        case _:
                            raise Exception("Impossible!")
                case _:
                    raise Exception(f"Binary operator not allowed on these operands: {v1}, {v2}")
        case EIf(test, body, orelse):
            v1 = eval_expr(env, test)
            if v1:
                return eval_expr(env, body)
            else:
                return eval_expr(env, orelse)
        case EInput():
            while True:
                try:
                    res = int(input())
                    return simulate_over_and_underflow(res)
                except ValueError:
                    continue
        case ETuple(es):
            return VTuple([eval_expr(env, e) for e in es])
        case ETupleAccess(e, i):
            match eval_expr(env, e):
                case VTuple(vs):
                    return vs[i]
                case _:
                    raise Exception("Tried to index into a non-tuple value.")
        case ETupleLen(e):
            match eval_expr(env, e):
                case VTuple(vs):
                    return len(vs)
                case _:
                    raise Exception("Tried to get length of non-tuple value.")
        case ECall(func, args):
            f = eval_expr(env, func)
            xs = tuple(eval_expr(env, x) for x in args)
            # funs can return none, so no need to worry abour returning it if apply_fun does so
            return apply_fun(f, xs)
        case ELambda(xs, expr):
            return VFunction(Id("lambda"), xs, ilist(SReturn(expr)), env)
        case EField(e, name):
            obj = eval_expr(env, e)
            match obj:
                case VObject(_, fields):
                    return fields[name]
                case _:
                    raise Exception(f"Tried field access on non-object {obj}")
        # to interpret method calls
        # TODO: we need to eval the args before passing, as apply_fun expects a Value
        case EMethod(e, name, args):
            obj = eval_expr(env, e)
            match obj:
                case VObject(classref, fields):
                    for method in classref.methods:
                        match method:
                            case VFunction() if name == method.name:
                                evals = []
                                evals.append(obj)
                                for arg in args:
                                    evals.append(eval_expr(env, arg))
                                args = tuple(evals)
                                return apply_fun(method, args)
                            case _:
                                raise Exception("method is not callable")
                    raise Exception(f"Could not find the method {name} in class {classref.name}")
                case _:
                    raise Exception("Method Call on non-class object")

        # case EArity(expr):
        #     v = eval_expr(env, expr)
        #     match v:
        #         case VFunction(_, xs, _, _):
        #             return len(xs)
        #         case _:
        #             raise Exception(f"Tried to take arity of non function {pretty_expr(expr)}")

def eval_stmts(env: RTEnv, ss: IList[Stmt]) -> Optional[Value]:
    for s in ss:
        match s:
            case SExpr(e):
                eval_expr(env, e)
            case SPrint(e):
                print(eval_expr(env, e))
            case SAssign(x, _, e):
                match x:
                    case Id():
                        assign(env, x, eval_expr(env, e))
                    case EField(fieldexpr, name):
                        obj = eval_expr(env, fieldexpr)
                        res = eval_expr(env, e)
                        match obj:
                            case VObject(classref, fields):
                                if name not in fields.keys():
                                    raise Exception(f"class {classref.name} has no field {name}")
                                fields[name] = res
                            case _:
                                raise Exception(f"{obj} is not a class object")
            case SIf(test, body, orelse):
                tv = eval_expr(env, test)
                match eval_stmts(env, body) if tv else eval_stmts(env, orelse):
                    case None:
                        continue
                    case rv:
                        return rv
            case SWhile(test, body):
                while eval_expr(env, test):
                    match eval_stmts(env, body):
                        case None:
                            continue
                        case rv:
                            return rv
            case SReturn(e):
                return eval_expr(env, e)
            case SRaise(e):
                raise UserException(eval_expr(env, e))
            case STry(body, x, handler):
                try:
                    r = eval_stmts(env, body)
                    if r is not None:
                        return r
                except UserException as ex:
                    match ex:
                        case UserException(v):
                            assign(env, x, v)
                            r = eval_stmts(env, handler)
                            if r is not None:
                                return r
            case SClass(name, super, fields, methods):
                match super:
                    case None:
                        pass
                    case TClass(n, _, _, _):
                        try:
                            lookup(env, n)
                        except:
                            raise Exception(f"parent class {n} could not be found")
                    case TInt() | TBool():
                        pass
                    case _:
                        raise Exception(f"parent class {super} can not be inherited from")
                fieldIds = IList([x[0] for x in fields])
                vmethods = []
                for method in methods:
                    vfun = VFunction(method.name, IList([m[0] for m in method.params]), method.body, env)
                    vmethods.append(vfun)
                cv = VClass(name, super, fieldIds, IList(vmethods))
                try:
                    lookup(env, name)
                except Exception:
                    assign(env, name, cv)
                else:
                    raise Exception(f"interpreter found multiple definotons of class {name}")

def eval_decls(env: RTEnv, defs: IList[Decl]):
    for d in defs:
        match d:
            case DFun(f, parms, _, body):
                fv = VFunction(f, IList([x for (x, _) in parms]), body, env)
                assign(env, f, fv)

def eval_prog(p: Program):
    env: RTEnv = RTEnv(dict(), None)
    try:
        eval_stmts(env, p.classes)
    except UserException as e:
        print(e.value)
    print(f"successful class eval. env: {env}")
    eval_decls(env, p.decls)
    try:
        eval_stmts(env, p.main_body)
    except UserException as e:
        print(e.value)
