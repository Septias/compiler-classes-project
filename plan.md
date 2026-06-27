
# Plan: Add Python Dictionary Support

## Context

The project already has full class/OOP support. The next feature is Python `dict[K, V]` support. Dictionaries need:
- Runtime-computed key lookup (unlike tuple's constant-index access)
- Variable size with rehashing
- GC integration so dict values that are heap objects (tuples, class instances) are correctly traced

**Design decisions:**
- Keys restricted to `int` (hash stability: pointer keys would be invalidated by GC copying them)
- Values can be any type (int, bool, tuple, class instance) — fully GC-traced
- Dict represented as two GC-managed tuples: a wrapper and a flat backing array
- Hash logic implemented in `runtime.c`, which directly manipulates GC globals
- Initial capacity: fixed at 16 slots; resizing on insert when load > 0.7

**Dict memory layout:**

Dict wrapper (GC tuple, 3 words after metadata):
```
[metadata: 3 << 1]
[count << 1]         ← tagged int, GC ignores
[capacity << 1]      ← tagged int, GC ignores
[backing_ptr | 1]    ← tagged heap pointer, GC traces
```

Backing array (GC tuple, 3*capacity words after metadata):
```
[metadata: (3*capacity) << 1]
[flag0: 0 or 2]  ← 0=empty, 2=occupied; GC ignores (LSB=0)
[key0]           ← tagged int or 0 if empty; GC ignores int values
[val0]           ← any tagged value; GC traces if heap pointer (LSB=1)
...              ← repeated for each slot
```

The existing GC requires no changes: it traces words with LSB=1 (tagged heap pointers) and ignores words with LSB=0 (ints, empty slots).

---

## Implementation Steps

### Step 1: `src/types_.py`
Add `TDict(key_ty, val_ty)` dataclass.
Update `type Type = ... | TDict`.
Add case to `pretty_type()`.

### Step 2: `src/ast_1_python.py`
Add expression nodes:
- `EDict(items: IList[tuple[Expr, Expr]])` — dict literal `{k: v, ...}`
- `EDictAccess(e: Expr, key: Expr)` — subscript `d[key]`

Update:
- `Expr` union type to include `EDict | EDictAccess`
- `SAssign.lhs: Id | EField | EDictAccess` (allow dict subscript on LHS)

### Step 3: `src/pass_0_1_parser.py`
- Parse `ast.Dict(keys, values)` → `EDict`
- Parse `ast.Subscript(e, key)` where subscript type isn't a constant int → `EDictAccess`
- Parse `ast.Subscript` on LHS of assign → `SAssign(EDictAccess(...), ...)`
- Parse `dict[K, V]` type annotation → `TDict`

### Step 4: `src/type_checker.py`
- Type-check `EDict`: infer/validate key type is `TInt`, infer value type from items
- Type-check `EDictAccess`: verify `e: TDict`, `key: TInt`, return `val_ty`
- Type-check `SAssign` with `EDictAccess` LHS: check value type matches `val_ty`
- Type-check constructor `dict[int, T]()`

### Step 5: `src/semantics.py`
- `EDict` → Python `dict` at interpreter level
- `EDictAccess` → Python dict subscript
- Dict assignment in `exec_stmt`

### Step 6: `src/ast_2_shrunk.py` (and ast_3 through ast_8)
Add `EDict` / `EDictAccess` nodes to each intermediate AST. Keep same structure (no transformation yet).
Update `SAssign.lhs` to allow `EDictAccess` (in shrunk form).

### Step 7: Thread through passes (pass_1_2_shrink.py through pass_7_8_explicate.py)
Each pass adds trivial forwarding cases for `EDict` and `EDictAccess`, analogous to how `EInput` is passed through. Passes to update:
- `pass_1_2_shrink.py` — also update `shrink_stmt` for dict-assign
- `pass_2_2_uniquify.py` — uniquify variable names in dict key/value exprs
- `pass_2_3_reveal_functions.py`
- `pass_3_4_convert_assignments.py` — introduce `LDictSet(dict_expr, key_expr)` as new LHS form, or lower dict assignment to a statement `SDictSet(dict, key, val)`
- `pass_4_5_closure_conversion.py`
- `pass_5_6_alloc.py` — `EDict` becomes allocation of wrapper + backing array (similar to ETuple expansion, with GC check)
- `pass_6_7_monadic.py` — atomize dict key exprs
- `pass_7_8_explicate.py`

### Step 8: `src/pass_8_9_select.py` — Instruction selection

Map dict operations to C runtime calls:

```python
# EDict after alloc pass becomes: wrapper and backing array are pre-allocated GC objects
# dict_create sets up the metadata and zeros the backing array
case src.SAssign(lhs, src.EDictCreate(capacity)):
    lhs_out = select_lhs(lhs)
    return ilist(
        tgt.Move(a0, select_atom(backing_ptr)),   # pre-allocated backing array
        tgt.Move(a1, tgt.Const(capacity, '64bit')),
        tgt.Call(Label("dict_init"), 2, 'normal'),  # zero the backing array
        tgt.Move(a0, select_atom(wrapper_ptr)),
        tgt.Move(lhs_out, a0),
    )

# EDictGet: d[key]
case src.SAssign(lhs, src.EDictGet(e_dict, e_key)):
    lhs_out = select_lhs(lhs)
    return ilist(
        tgt.Move(a0, select_atom(e_dict)),
        tgt.Move(a1, select_atom(e_key)),
        tgt.Call(Label("dict_get"), 2, 'normal'),
        tgt.Move(lhs_out, a0),
    )

# SDictSet: d[key] = val
case src.SDictSet(e_dict, e_key, e_val):
    return ilist(
        tgt.Move(a0, select_atom(e_dict)),
        tgt.Move(a1, select_atom(e_key)),
        tgt.Move(a2, select_atom(e_val)),
        tgt.Call(Label("dict_set"), 3, 'normal'),
    )
```

### Step 9: `runtime/runtime.c`
Add C functions that operate on GC-managed dict objects (they know the layout):

```c
// Dict wrapper layout: [metadata][count<<1][capacity<<1][backing_ptr|1]
// Backing array layout: [metadata][(flag,key,val) * capacity]
//   flag: 0=empty, 2=occupied

// Initialize a pre-allocated backing array (zero all flag words)
void dict_init(int64_t* backing, uint64_t capacity);

// Look up key in dict, return tagged value (or raise exception if not found)
int64_t dict_get(int64_t* dict_wrapper, int64_t tagged_key);

// Insert or update key->value in dict
// Returns 1 if successful, 0 if dict is full (caller must resize)
int64_t dict_set(int64_t* dict_wrapper, int64_t tagged_key, int64_t tagged_val);

// Check if key exists
int64_t dict_has(int64_t* dict_wrapper, int64_t tagged_key);
```

Hash function: `tagged_key / 2 % capacity` (untagged int mod capacity).

Linear probing: probe `(hash + i) % capacity` for `i = 0, 1, 2, ...`.

### Step 10: Add tests in `tests/9_dict/`
- `basic.py` — create dict, set and get values
- `overwrite.py` — overwrite an existing key
- `function_arg.py` — pass dict to a function
- `class_value.py` — dict with class instance values (tests full GC support)
- `large.py` — test with many entries

---

## Key Files

| File | Change |
|---|---|
| `src/types_.py` | Add `TDict` |
| `src/ast_1_python.py` | Add `EDict`, `EDictAccess`, update `SAssign` |
| `src/ast_2_shrunk.py` — `src/ast_8_exp.py` | Add matching nodes to each AST |
| `src/pass_0_1_parser.py` | Parse dict syntax |
| `src/type_checker.py` | Validate dict operations |
| `src/semantics.py` | Interpret dicts |
| `src/pass_1_2_shrink.py` — `src/pass_7_8_explicate.py` | Forward-through for new nodes |
| `src/pass_5_6_alloc.py` | Expand `EDict` to backing array + wrapper allocation |
| `src/pass_8_9_select.py` | Emit calls to `dict_get`, `dict_set`, `dict_init` |
| `runtime/runtime.c` | Implement hash table operations on GC objects |
| `tests/9_dict/*.py` | New test cases |

## Verification

1. Existing tests still pass: `./do test`
2. Interpreter: `python3.12 src/interpreter.py tests/9_dict/basic.py`
3. Compiled: `./do run tests/9_dict/basic.py`
4. GC test: `./do run tests/9_dict/class_value.py` (dict with heap object values, forces GC)
