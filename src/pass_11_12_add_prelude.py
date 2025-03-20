import ast_11_patched as src
import ast_12_riscv as tgt
from register import *
from register_allocation import RegAllocOutput
from util.immutable_list import ilist, IList

def add_prelude_and_conclusion(
    p: src.Program,
    reg_allocs: dict[Label, RegAllocOutput],
) -> tgt.Program:
    out: tgt.Program = ilist()
    for f in p:
        out += apc_fun(f, reg_allocs)
    return out

def apc_fun(
    f: src.Function,
    reg_allocs: dict[Label, RegAllocOutput],
) -> tgt.Program:
    is_main = f.entry_label == Label("main")
    reg_alloc = reg_allocs[f.entry_label]

    prelude = compute_prelude(reg_alloc, is_main)
    conclusion = compute_conclusion(reg_alloc, is_main, False)

    f.body[f.entry_label] = prelude + f.body[f.entry_label]
    f.body[f.end_label] = f.body[f.end_label] + conclusion

    out: tgt.Program = ilist()

    for label, block in f.body.items():
        if label == f.entry_label:
            out += ilist(
                tgt.DGlobal(f.entry_label),
                tgt.DAlign(8),
            )
        out += ilist(label)
        for i in block:
            match i:
                case src.TailJump(rl) | src.TailJumpIndirect(rl):
                    out += compute_conclusion(reg_alloc, False, True)

                    # Skip the first two instructions of the function's
                    # prelude, i.e. storing fp and ra to stack, because
                    # the current function already stored them there.
                    # Note that the `.align 8` ensures that functions
                    # start at an address that's a multiple of 8, but
                    # not that the instructions of the function are aligned
                    # by 8. An instruction is encoded by 4 bytes, and
                    # multiple instructions are tightly packed together,so
                    # we choose offset 8 to skip 2 instructions.
                    offset = 8
                    match rl:
                        case src.Register(_) as r:
                            out += ilist(tgt.JumpIndirect(r, offset))
                        case src.Label(_) as l:
                            out += ilist(tgt.LoadAddress(t0, l))
                            out += ilist(tgt.JumpIndirect(t0, offset))
                case _:
                    out += ilist(i)

    return out

def compute_prelude(
    reg_alloc: RegAllocOutput,
    is_main: bool,
) -> IList[tgt.Instr]:
    offset_sp_aligned = aligned_offset(reg_alloc.offset_sp)

    prelude = ilist()

    prelude += ilist(
        tgt.Store(ra, tgt.Offset(sp, -8)),
        tgt.Store(fp, tgt.Offset(sp, -16)),
    )

    offset = 16
    for r in reg_alloc.callee_saved:
        offset += 8
        prelude += ilist(tgt.Store(r, tgt.Offset(sp, -offset)))

    for i in range(offset, offset_sp_aligned, 8):
        prelude += ilist(tgt.Store(zero, tgt.Offset(sp, -i-8)))

    prelude += ilist(
        tgt.IInstr2("addi", fp, sp, 0),
        tgt.IInstr2("addi", sp, sp, -offset_sp_aligned),
    )

    if is_main:
        # Zero all calle saved registers in main, such that
        # other functions called by main don't spill registers with
        # untagged values, and break the garbage collector.
        for r in set(CALLEE_SAVED_REGISTERS) - {sp, fp}:
            prelude += ilist(tgt.RInstr('add', r, zero, zero))
        prelude += ilist(
            # Call the garbage collector initialization function
            # Argument 1 is stack_begin, so we use the framepointer, i.e.
            # the stack pointer when main was called.
            tgt.IInstr2("addi", a0, fp, -8 * (2 + len(reg_alloc.callee_saved))),
            # Argument 2 is the initial size for from- and to-space in words
            tgt.IInstr1("li", a1, 8),
            # Call gc init
            tgt.Call(Label("gc_init")),
        )

    return prelude

def compute_conclusion(
    reg_alloc: RegAllocOutput,
    is_main: bool,
    is_tail_call: bool,
) -> IList[tgt.Instr]:
    offset_sp_aligned = aligned_offset(reg_alloc.offset_sp)

    conclusion = ilist()

    if is_main:
        conclusion += ilist(
            tgt.IInstr2("addi", a0, zero, 0),
        )

    conclusion += ilist(
        tgt.IInstr2("addi", sp, sp, offset_sp_aligned),
    )

    if not is_tail_call:
        conclusion += ilist(
            tgt.Load(ra, tgt.Offset(sp, -8)),
            tgt.Load(fp, tgt.Offset(sp, -16)),
        )

    offset = 16
    for r in reg_alloc.callee_saved:
        offset += 8
        conclusion += ilist(tgt.Load(r, tgt.Offset(sp, -offset)))

    if not is_tail_call:
        conclusion += ilist(tgt.Return())

    return conclusion

def aligned_offset(offset_sp):
    # Standard RISC-V calling convention wants us to keep the stack
    # pointer sp a multiple of 16. If our stack frame's size is already a
    # multiple of 16, then we're good, otherwise we round its size up to
    # the next multiple of 16 (which amounts to having a bit of unused
    # space in the stack frame).
    return align(16, offset_sp)

def align(alignment: int, n: int) -> int:
    return n if n % alignment == 0 else (n // alignment + 1) * alignment
