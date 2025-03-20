import ast_9_sel as src
import ast_10_mem as tgt
from register import *
from register_allocation import RegAllocOutput
from util.immutable_list import ilist, IList

# BEGIN
def assign_homes(
    p: src.Program,
    reg_info: dict[src.Label, RegAllocOutput],
) -> tgt.Program:
    return IList([assign_homes_fun(d, reg_info) for d in p])

def assign_homes_fun(
    f: src.Function,
    reg_info: dict[src.Label, RegAllocOutput],
) -> tgt.Function:
    return tgt.Function(
        f.entry_label,
        f.start_label,
        f.end_label,
        assign_homes_body(f.body, reg_info[f.entry_label].env),
    )

def assign_homes_body(
    blocks: src.Blocks,
    env: dict[src.Id, tgt.Register | tgt.Offset],
) -> tgt.Blocks:
    out: tgt.Blocks = {}
    for label, block in blocks.items():
        block_out: tgt.Block = ilist()
        for i in block:
            block_out += ilist(assign_homes_instr(env, i))
        out[label] = block_out
    return out
# END

def assign_homes_instr(
    env: dict[src.Id, tgt.Register | tgt.Offset],
    i: src.Instr,
) -> tgt.Instr:
    match i:
        case src.Jump(label):
            return tgt.Jump(label)
        case src.JumpIndirect(r):
            return tgt.JumpIndirect(r)
        case src.Branch(cc, rs1, rs2, target):
            return tgt.Branch(cc, assign_home_src(env, rs1), assign_home_src(env, rs2), target)
        case src.Move(dst, src_):
            return tgt.Move(assign_home_dst(env, dst), assign_home_src(env, src_))
        case src.Call(src_, _, is_tail_call):
            return tgt.Call(assign_home_src(env, src_), is_tail_call)
        case src.Instr2(op, dst, src1, src2):
            return tgt.Instr2(
                op,
                assign_home_dst(env, dst),
                assign_home_src(env, src1),
                assign_home_src(env, src2),
            )

def assign_home_dst(
    env: dict[src.Id, tgt.Register | tgt.Offset],
    arg: src.ArgWrite,
) -> tgt.ArgWrite:
    match arg:
        case src.Id(_) as x:
            return assign_home_id(env, x)
        case src.Register(r):
            return tgt.Register(r)
        case src.Offset(e, i):
            match e:
                case src.Register(r):
                    return tgt.Offset(tgt.Register(r), i)
                case src.Label(l):
                    return tgt.Offset(tgt.Label(l), i)
                case src.Id(_) as x:
                    return tgt.Offset(assign_home_id(env, x), i)

def assign_home_src(
    env: dict[src.Id, tgt.Register | tgt.Offset],
    arg: src.ArgRead
) -> tgt.ArgRead:
    match arg:
        case src.Const(i, size):
            return tgt.Const(i, size)
        # BEGIN
        case src.Label(l):
            return tgt.Label(l)
        # END
        case _:
            return assign_home_dst(env, arg)

def assign_home_id(
    env: dict[src.Id, tgt.Register | tgt.Offset],
    x: src.Id,
) -> tgt.Register | tgt.Offset:
    if x not in env:
        raise Exception(
            f"Expected {x} to have either a register or stack location assigned!"
        )
    return env[x]
