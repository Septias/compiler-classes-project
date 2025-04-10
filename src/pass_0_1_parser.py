from dataclasses import dataclass
from typing import Any, Sequence
import ast

from ast_1_python import *
from identifier import Id
from util.immutable_list import IList, ilist

# as classes baheve like types and types are parsed statically, we need to keep track of all defined classes and their fields
type Cctx = dict[Id, IList[tuple[Id, Type]]]

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

@dataclass(frozen=True)
class UnknownTypeError(ParseError):
    typename: str

    def __str__(self) -> str:
        return f"a (class)type with the name {self.typename} was not found"

def map_node(node: ast.AST, ctx: Cctx) -> Any:
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
            return EOp1(map_node(op, ctx), map_node(operand, ctx))
        case (
            ast.BinOp(left, op, right)
            | ast.BoolOp(op, [left, right])
            | ast.Compare(left, [op], [right])
        ):
            return EOp2(map_node(left, ctx), map_node(op, ctx), map_node(right, ctx))
        case ast.If(test, body, orelse):
            return SIf(map_node(test, ctx), map_nodes(body, ctx), map_nodes(orelse, ctx))
        case ast.IfExp(test, body, orelse):
            return EIf(map_node(test, ctx), map_node(body, ctx), map_node(orelse, ctx))
        case ast.While(test, body, []):
            return SWhile(map_node(test, ctx), map_nodes(body, ctx))
        case ast.Assign([ast.Name(x)], value, _):
            return SAssign(Id(x), None, map_node(value, ctx))
        case ast.AnnAssign(ast.Name(x), ty, value) if value is not None:
            return SAssign(Id(x), map_type_node(ty, ctx), map_node(value, ctx))
        # case ast.Assign([ast.Subscript(e, ast.Constant(int(i)), _)], value, _):
        #     return SAssign(LSubscript(map_node(e), i), map_node(value))
        case ast.Call(ast.Name("input_int"), [], keywords) if len(keywords) == 0:
            return EInput()
        case ast.Expr(ast.Call(ast.Name("print"), [arg], keywords)) if len(keywords) == 0:
            return SPrint(map_node(arg, ctx))
        case ast.Tuple(elts, _):
            return ETuple(map_nodes(elts, ctx))
        case ast.Subscript(e, ast.Constant(int(i)), _):
            return ETupleAccess(map_node(e, ctx), i)
        case ast.Call(ast.Name("len"), [arg], keywords) if len(keywords) == 0:
            return ETupleLen(map_node(arg, ctx))
        case ast.Expr(value):
            return SExpr(map_node(value, ctx))
        case ast.FunctionDef(name, args, body, _, returns, _, _):
            params = []
            for arg in args.args:
                if arg.annotation is None:
                    raise UnsupportedFeature(node)
                else:
                    id = Id(arg.arg)
                    ty = map_type_node(arg.annotation, ctx)
                    params.append((id, ty))
            if returns is None:
                ret_ty = TNone()
            else:
                ret_ty = map_type_node(returns, ctx)
            return DFun(Id(name), IList(params), ret_ty, map_nodes(body, ctx))
        case ast.Return(e):
            match e:
                case None:
                    return SReturn(EConst(None))
                case _:
                    return SReturn(map_node(e, ctx))
        case ast.Lambda(args, body):
            params = IList([Id(arg.arg) for arg in args.args])
            return ELambda(params, map_node(body, ctx))
        case ast.Call(e, args, keywords) if len(keywords) == 0:
            return ECall(map_node(e, ctx), map_nodes(args, ctx))
        case ast.Raise(ast.Call(_, [arg])):
            return SRaise(map_node(arg, ctx))
        case ast.Try(body, [ast.ExceptHandler(ast.Name("Exception"), x, ex_body)], [], []) if x is not None:
            return STry(map_nodes(body, ctx), Id(x), map_nodes(ex_body, ctx))
        # map classes
        case ast.ClassDef(name, _, _, body, _):
            params = []
            for classop in body:
                match classop:
                    # attribute of class is being defined
                    case ast.AnnAssign(ast.Name(id, _), annot, _, _):
                        ty = map_type_node(annot, ctx)
                        params.append((Id(id), ty))
                    case ast.FunctionDef():
                        raise UnsupportedFeature(node)
            ctx[Id(name)] = IList(params)
            return SClass(Id(name), IList(params))
        case ast.Attribute(e, id):
            return EField(map_node(e, ctx), Id(id))
        case _:
            raise UnsupportedFeature(node)

def map_nodes(nodes: Sequence[Any], ctx: Cctx) -> IList[Any]:
    return IList([map_node(node, ctx) for node in nodes])

def map_type_node(node: ast.AST, ctx: Cctx) -> Type:
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
                    return TTuple(map_type_nodes(sls, ctx))
                case _:
                    return TTuple(ilist(map_type_node(sl, ctx)))
        case ast.Subscript(ast.Name("Callable"), ast.Tuple([ast.List(params), ret])):
            return TCallable(map_type_nodes(params, ctx), map_type_node(ret, ctx))
        case ast.Name(classname, _):
            if Id(classname) in ctx:
                return TClass(Id(classname), ctx[Id(classname)])
            else:
                raise UnknownTypeError(classname)
        case _:
            raise UnsupportedFeature(node)

def map_type_nodes(nodes: Sequence[Any], ctx: Cctx) -> IList[Type]:
    return IList([map_type_node(node, ctx) for node in nodes])

def parse(src_str: str) -> Program:
    decls = []
    body = []
    ctx: Cctx = dict()
    for n in map_nodes(ast.parse(src_str).body, ctx):
        match n:
            case DFun(_, _, _, _):
                decls.append(n)
            case _:
                body.append(n)
    return Program(IList(decls), IList(body))
