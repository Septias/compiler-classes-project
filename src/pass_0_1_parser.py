from dataclasses import dataclass
from typing import Any, Sequence
import ast

from ast_1_python import *
from identifier import Id
from util.immutable_list import IList, ilist

@dataclass(frozen=True)
class ParseError(Exception):
    pass

@dataclass(frozen=True)
class UnsupportedFeature(ParseError):
    node: Any

    def __str__(self) -> str:
        return f"Found unsupported AST node {self.node} that represents `{ast.unparse(self.node)}`\n\n `{ast.dump(self.node, indent=4)}`"

@dataclass(frozen=True)
class IllegalName(ParseError):
    name: str

    def __str__(self) -> str:
        return f"The `name` {self.name} is not a valid variable name, use only letters and numbers"

def map_node(node: ast.AST) -> Any:
    match node:
        case ast.Add():
            return "+"
        case ast.Sub() | ast.USub():
            return "-"
        case ast.Eq():
            return "=="
        case ast.NotEq():
            return "!="
        case ast.Lt():
            return "<"
        case ast.LtE():
            return "<="
        case ast.Gt():
            return ">"
        case ast.GtE():
            return ">="
        case ast.And():
            return "and"
        case ast.Or():
            return "or"
        case ast.Not():
            return "not"
        case ast.Is():
            return "is"
        case ast.Constant(value) if type(value) is int:
            return EConst(value)
        case ast.Constant(value) if type(value) is bool:
            return EConst(value)
        case ast.Name(id, _):
            if not all([(c.isalnum() or c == "_") for c in id]):
                raise IllegalName(id)
            return EVar(Id(id))
        case ast.UnaryOp(op, operand):
            return EOp1(map_node(op), map_node(operand))
        case (
            ast.BinOp(left, op, right)
            | ast.BoolOp(op, [left, right])
            | ast.Compare(left, [op], [right])
        ):
            return EOp2(map_node(left), map_node(op), map_node(right))
        case ast.If(test, body, orelse):
            return SIf(map_node(test), map_nodes(body), map_nodes(orelse))
        case ast.IfExp(test, body, orelse):
            return EIf(map_node(test), map_node(body), map_node(orelse))
        case ast.While(test, body, []):
            return SWhile(map_node(test), map_nodes(body))
        case ast.Assign([ast.Name(x)], value, _):
            return SAssign(Id(x), None, map_node(value))
        case ast.AnnAssign(ast.Name(x), ty, value) if value is not None:
            return SAssign(Id(x), map_type_node(ty), map_node(value))
        # case ast.Assign([ast.Subscript(e, ast.Constant(int(i)), _)], value, _):
        #     return SAssign(LSubscript(map_node(e), i), map_node(value))
        case ast.Call(ast.Name("input_int"), [], keywords) if len(keywords) == 0:
            return EInput()
        case ast.Expr(ast.Call(ast.Name("print"), [arg], keywords)) if len(keywords) == 0:
            return SPrint(map_node(arg))
        case ast.Tuple(elts, _):
            return ETuple(map_nodes(elts))
        case ast.Subscript(e, ast.Constant(int(i)), _):
            return ETupleAccess(map_node(e), i)
        case ast.Call(ast.Name("len"), [arg], keywords) if len(keywords) == 0:
            return ETupleLen(map_node(arg))
        case ast.Expr(value):
            return SExpr(map_node(value))
        case ast.FunctionDef(name, args, body, _, returns, _, _):
            params = []
            for arg in args.args:
                if arg.annotation is None:
                    raise UnsupportedFeature(node)
                else:
                    id = Id(arg.arg)
                    ty = map_type_node(arg.annotation)
                    params.append((id, ty))
            if returns is None:
                ret_ty = TNone()
            else:
                ret_ty = map_type_node(returns)
            return DFun(Id(name), IList(params), ret_ty, map_nodes(body))
        case ast.Return(e):
            match e:
                case None:
                    return SReturn(EConst(None))
                case _:
                    return SReturn(map_node(e))
        case ast.Lambda(args, body):
            params = IList([Id(arg.arg) for arg in args.args])
            return ELambda(params, map_node(body))
        case ast.Call(e, args, keywords) if len(keywords) == 0:
            return ECall(map_node(e), map_nodes(args))
        case ast.Raise(ast.Call(_, [arg])):
            return SRaise(map_node(arg))
        case ast.Try(body, [ast.ExceptHandler(ast.Name("Exception"), x, ex_body)], [], []) if x is not None:
            return STry(map_nodes(body), Id(x), map_nodes(ex_body))
        # map classes
        case ast.ClassDef(name, _, _, body, _):
            params = []
            for classop in body:
                match classop:
                    # attribute of class is being defined
                    case ast.AnnAssign(ast.Name(id, _), annot, _, _):
                        ty = map_type_node(annot)
                        params.append((Id(id), ty))
                    case ast.FunctionDef():
                        raise UnsupportedFeature(node)
            return SClass(Id(name), IList(params))
        case ast.Attribute(e, id):
            return EField(map_node(e), Id(id))
        case _:
            raise UnsupportedFeature(node)

def map_nodes(nodes: Sequence[Any]) -> IList[Any]:
    return IList([map_node(node) for node in nodes])

def map_type_node(node: ast.AST) -> Type:
    match node:
        case ast.Name("int", _):
            return TInt()
        case ast.Name("bool", _):
            return TBool()
        case ast.Name("NoneType", _) | None:
            return TNone()
        case ast.Subscript(ast.Name("tuple"), sl):
            match sl:
                case ast.Tuple(sls):
                    return TTuple(map_type_nodes(sls))
                case _:
                    return TTuple(ilist(map_type_node(sl)))
        case ast.Subscript(ast.Name("Callable"), ast.Tuple([ast.List(params), ret])):
            return TCallable(map_type_nodes(params), map_type_node(ret))
        case _:
            raise UnsupportedFeature(node)

def map_type_nodes(nodes: Sequence[Any]) -> IList[Type]:
    return IList([map_type_node(node) for node in nodes])

def parse(src_str: str) -> Program:
    decls = []
    body = []
    for n in map_nodes(ast.parse(src_str).body):
        match n:
            case DFun(_, _, _, _):
                decls.append(n)
            case _:
                body.append(n)
    return Program(IList(decls), IList(body))
