from dataclasses import dataclass
from util.immutable_list import IList

# Type Syntax

type Type = TBool | TInt | TNone | TTuple | TCallable

@dataclass(frozen=True)
class TBool:
    pass

@dataclass
class TInt:
    pass

@dataclass
class TNone:
    pass

@dataclass
class TTuple:
    ts: IList[Type]

@dataclass
class TCallable:
    param_tys: IList[Type]
    ret_ty: Type

# Pretty Printing

def pretty_type(t: Type) -> str:
    match t:
        case TBool():
            return "bool"
        case TInt():
            return "int"
        case TNone():
            return "NoneType"
        case TTuple(ts):
            return f"tuple[{pretty_types(ts)}]"
        case TCallable(param_tys, ret_ty):
            return f"Callable[[{pretty_types(param_tys)}], {pretty_type(ret_ty)}]"

def pretty_types(ts: IList[Type]) -> str:
    return ", ".join(pretty_type(t) for t in ts)
