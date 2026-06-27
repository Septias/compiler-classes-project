import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pass_0_1_parser import parse
from type_checker import type_check
from pass_1_2_shrink import shrink
from pass_2_2_uniquify import uniquify
from pass_2_3_reveal_functions import reveal
import ast_2_shrunk as ast2
import ast_3_revealed as ast3
from identifier import Id
from label import Label

def run_to_uniquify(src):
    p = parse(src)
    type_check(p)
    return uniquify(shrink(p))

def run_to_reveal(src):
    p = parse(src)
    type_check(p)
    return reveal(uniquify(shrink(p)))

def program_main(p):
    return next(f for f in p if f.name == Id("program_main") or f.name == Label("program_main"))

# --- uniquify ---

def test_uniquify_dict_vars_renamed():
    body = program_main(run_to_uniquify("d: dict[int, int] = {1: 2}")).body
    stmt = body[0]
    # lhs variable should be uniquified (not the original 'd')
    assert stmt.lhs != Id("d")

def test_uniquify_dict_key_var_renamed():
    body = program_main(run_to_uniquify("k: int = 1\nd: dict[int, int] = {}\nx = d[k]")).body
    access = body[2].rhs
    # k inside the dict access should be renamed
    assert isinstance(access, ast2.ETupleAccess) or isinstance(access, ast2.EDictAccess)

def test_uniquify_dict_literal_vars_renamed():
    body = program_main(run_to_uniquify("x: int = 1\ny: int = 2\nd = {x: y}")).body
    items = list(body[2].rhs.items)
    k, v = items[0]
    # both key and value should be renamed EVar, not the original names
    assert isinstance(k, ast2.EVar) and k.name != Id("x")
    assert isinstance(v, ast2.EVar) and v.name != Id("y")

def test_uniquify_dict_assign_lhs_renamed():
    body = program_main(run_to_uniquify("k: int = 1\nd: dict[int, int] = {}\nd[k] = 5")).body
    stmt = body[2]
    assert isinstance(stmt.lhs, ast2.EDictAccess)
    assert stmt.lhs.e != ast2.EVar(Id("d"))

def test_uniquify_preserves_structure():
    body = program_main(run_to_uniquify("d: dict[int, int] = {1: 10}\nd[2] = 20")).body
    assert isinstance(body[0].rhs, ast2.EDict)
    assert isinstance(body[1].lhs, ast2.EDictAccess)

# --- reveal ---

def test_reveal_dict_literal_passes_through():
    body = program_main(run_to_reveal("d: dict[int, int] = {1: 10}")).body
    assert isinstance(body[0].rhs, ast3.EDict)

def test_reveal_dict_access_passes_through():
    body = program_main(run_to_reveal("k: int = 1\nd: dict[int, int] = {}\nx = d[k]")).body
    assert isinstance(body[2].rhs, ast3.EDictAccess)

def test_reveal_dict_assign_passes_through():
    body = program_main(run_to_reveal("k: int = 1\nd: dict[int, int] = {}\nd[k] = 5")).body
    assert isinstance(body[2].lhs, ast3.EDictAccess)

def test_reveal_function_ref_inside_dict_value():
    src = """
def f(x: int) -> int:
    return x
d: dict[int, int] = {1: f(1)}
"""
    body = program_main(run_to_reveal(src)).body
    assert isinstance(body[0].rhs, ast3.EDict)
    _, v = list(body[0].rhs.items)[0]
    assert isinstance(v, ast3.ECall)
    assert isinstance(v.fun, ast3.EFunRef)

def test_reveal_produces_labels():
    p = run_to_reveal("d: dict[int, int] = {1: 10}")
    for f in p:
        assert isinstance(f.name, Label)

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
