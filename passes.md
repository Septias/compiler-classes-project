
## AST 1 — ast_1_python (Python AST)

What it is: Faithful representation of the source language. Produced by the
parser (pass 0→1) from Python's own ast module.

Key features:
- Program has three parts: classes, decls, main_body (top-level statements
are separate)
- DFun.params carries type annotations: IList[tuple[Id, Type]]
- EConst has no size field (integers not yet tagged)
- Has EField, EMethod, SClass for OOP
- Op2 includes "and", "or", "is" (Python-specific operators)
- SAssign.lhs can be Id | EField, with optional type annotation
- ELambda has no fvs (free variables not yet computed)


## Pass 1→2 — Shrink

- Desugars and/or into EIf chains
- Desugars class definitions into flat standalone functions (method dispatch
via tuple/subscript)
- Wraps top-level statements in a program_main() function
- Creates a main() wrapper that calls program_main inside a STry to catch
unhandled exceptions
- Strips type annotations from DFun.params


## AST 2 — ast_2_shrunk

Diff from AST 1:
- Program is now IList[Decl] — flat list of functions, no separate classes/main_body
- DFun.name is Id (not yet a Label)
- EConst gains size: Literal['64bit', '63bit'] — tagged integers introduced
- EField, EMethod, SClass gone — desugared away
- Op2 drops "and", "or", "is"
- SAssign.lhs is Id | ETupleAccess with no type annotation


## Pass 2→2 — Uniquify

(Same AST 2 in, AST 2 out.) Renames all variables to unique names so scopes can't clash. No structural changes.


## Pass 2→3 — Reveal Functions

- Collects the set of all top-level function names
- Replaces EVar(f) where f is a top-level function with EFunRef(Label(f.name))
- Promotes DFun.name from Id → Label


## AST 3 — ast_3_revealed

Diff from AST 2:
- DFun.name is now Label
- EFunRef(fun: Label) added — distinguishes a "function pointer" from a
local variable


## Pass 3→4 — Convert Assignments (boxing)

For each function, computes AF = variables that are both assigned (mutated)
and captured by a lambda. These need to be "boxed" so that the closure and
outer scope share the same mutable cell:
- Wraps each AF variable in a 1-element tuple: x = (initial_value,)
- Rewrites all reads/writes of boxed vars as x[0]
- Annotates ELambda with its free variables (fvs)


## AST 4 — ast_4_conv_ass

Diff from AST 3:
- ELambda gains fvs: IList[Id]
- SAssign.lhs becomes the new typed union Lhs = LId | LSubscript (replaces
raw Id | ETupleAccess)


## Pass 4→5 — Closure Conversion

- Lifts each ELambda to a new top-level DFun
- Adds an extra first parameter closure to every function (including
existing top-level ones)
- The closure object is a tuple: (EFunRef(fn_label), fv1, fv2, ...)
- Calling a closure: extract the function pointer from closure[0], pass the
closure tuple as first arg
- EBegin(body, tail) is introduced to let tuple-building happen inside an
expression position


## AST 5 — ast_5_closures

Diff from AST 4:
- ELambda removed entirely
- EBegin(body: IList[Stmt], tail: Expr) added — sequences statements then
evaluates an expression

(Pass 5→5 — Limit Functions uses the same AST 5. It packs extra parameters
into a tuple if a function has more than 8 args, to stay within the calling
convention's register count.)


## Pass 5→6 — Allocate

Expands ETuple(es) into explicit GC-managed heap allocation:
1. Check if gc_free_ptr + size <= gc_fromspace_end; if not, emit SCollect
2. Emit EAllocate(n) to bump the free pointer and get a raw pointer
3. Write each element with LSubscript stores
4. EBegin is used to wrap these steps inside an expression


## AST 6 — ast_6_alloc

Diff from AST 5:
- ETuple removed
- EAllocate(num_elems: int) added — raw heap allocation
- EGlobal(var) added — reads GC global variables (gc_free_ptr,
gc_fromspace_end)
- SCollect(num_words: int) added — triggers GC


## Pass 6→7 — Monadic Normalization (ANF)

Flattens all expressions so that:
- Every operand is an atom (EConst or EVar)
- Complex sub-expressions are pulled out into temporaries (SAssign)
- EBegin is eliminated (its statements are lifted into the surrounding
context)
- SWhile's test expression is split: re-evaluation code becomes test_body:
IList[Stmt] plus test_expr: EOp2Comp
- Binary ops split into EOp2Arith and EOp2Comp (comparisons vs arithmetic)


## AST 7 — ast_7_mon

Diff from AST 6:
- ExprAtom = EConst | EVar — a separate type for atoms
- EOp2 split into EOp2Arith and EOp2Comp
- All operator operands typed as ExprAtom
- EBegin gone
- SExpr gone (no bare expression statements)
- SIf.test is specifically EOp2Comp
- SWhile gains test_body: IList[Stmt] + test_expr: EOp2Comp


## Pass 7→8 — Explicate Control Flow

Converts the flat statement list into an explicit control-flow graph:
- Each DFun body becomes dict[Label, Block] (basic blocks)
- SIf → two target-labelled blocks + conditional goto
- SWhile → loop block with goto
- SReturn at tail position → STailCall or plain SReturn
- STry → STryEnter/STryExit/SExcEnter nodes that manipulate the exception
handler stack


## AST 8 — ast_8_exp

Diff from AST 7:
- DFun body is now Blocks = dict[Label, Block] with start_label and
end_label
- SIf targets are Label instead of nested IList[Stmt]
- SGoto(target: Label) added
- STailCall(func, args) added
- STryEnter, STryExit, SExcEnter added
- SWhile gone (replaced by gotos)


## Pass 8→9 — Instruction Selection

Lowers each high-level statement to sequences of pseudo-RISC-V instructions.
Variables are still symbolic (Id), not yet placed in registers/memory. Key
mappings:
- EInput → call input_int64, multiply by 2 (add integer tag bit)
- SPrint → divide by 2 (strip tag), call print_int64
- Arithmetic → Instr2
- Comparisons → Branch
- Calls → move args into a0–a7, emit Call
- STailCall → TailCall (resolved later)
- STryEnter/STryExit → stack pointer / frame pointer saves


## AST 9 — ast_9_sel

Diff from AST 8:
- DFun becomes Function (no params field on the struct; param moves are
already in the start block)
- Instructions: Move, Call, Jump, JumpIndirect, Branch, Instr2
- Args: ArgWrite = Id | Register | Offset, ArgRead = ArgWrite | Label |
Const
- Id still used as pseudo-registers


## Pass 9→10 — Assign Homes

Uses register allocation results to replace every Id (pseudo-register) with
either a physical Register or a stack Offset(fp, n).


## AST 10 — ast_10_mem

Diff from AST 9:
- Id gone from all argument positions
- ArgWrite = Register | Offset, ArgRead = ArgWrite | Label | Const
- Instruction set unchanged; just all variables resolved to concrete
locations


## Pass 10→11 — Patch Instructions

Lowers pseudo-instructions to actual RISC-V instruction forms:
- Move(reg, reg) → add rd, zero, rs
- Move(reg, offset) → ld (load)
- Move(offset, ...) → sd (store), potentially via a scratch t0
- Move(reg, const) → li
- Move(reg, label) → la
- Call(..., 'tail call') → TailJump/TailJumpIndirect (pseudo, expanded in
next pass)
- Memory-to-memory moves are broken into two instructions via t0


## AST 11 — ast_11_patched

Diff from AST 10:
- Uses proper RISC-V instruction types from ast_12_riscv: RInstr, IInstr2,
IInstr1, Load, Store, LoadAddress
- Adds TailJump(target: Label) and TailJumpIndirect(target: Register)
pseudo-instructions
- Still organized as Function with Blocks


## Pass 11→12 — Add Prelude and Conclusion

Flattens the block structure into a linear instruction stream and adds
function frames:
- Prelude: save callee-saved registers, set up frame pointer; for main, also
initialize GC
- Conclusion: restore registers, ret
- Tail calls: emit epilogue (without restoring ra/fp — those stay from the
caller), then jump directly to callee
- Emits .globl and .align 8 directives
- Labels are emitted inline as Label instructions


## AST 12 — ast_12_riscv

Diff from AST 11:
- Program = IList[Instr] — completely flat linear instruction list, no
function/block structure
- All instruction types are concrete RISC-V: RInstr, IInstr2, IInstr1, Load,
Store, LoadAddress, Call, CallIndirect, Jump, JumpIndirect, Return, Branch
- Label appears inline as an instruction node (emitted as label:)
- DGlobal, DAlign assembler directives included
- Offset is register-only: Offset(reg: Register, offset: int)
- No Id, no TailJump pseudo-instructions — everything is real assembly
