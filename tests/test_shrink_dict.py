import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pass_0_1_parser import parse
from type_checker import type_check
from pass_1_2_shrink import shrink
from ast_2_shrunk import EDict, EDictAccess, SAssign, EVar, ETupleAccess
from identifier import Id

def shrink_prog(src):
    p = parse(src)
    type_check(p)
    return shrink(p)

def program_main(p2):
    return next(f for f in p2 if f.name.name == "program_main")

def test_dict_literal():
    body = program_main(shrink_prog("d: dict[int, int] = {1: 10, 2: 20}")).body
    assert isinstance(body[0].rhs, EDict)
    assert len(list(body[0].rhs.items)) == 2

def test_dict_access_variable_key():
    body = program_main(shrink_prog("k: int = 1\nd: dict[int, int] = {}\nx = d[k]")).body
    assert isinstance(body[2].rhs, EDictAccess)

def test_dict_access_const_key():
    # constant int key is parsed as ETupleAccess but shrink converts it to EDictAccess
    body = program_main(shrink_prog("d: dict[int, int] = {}\nx = d[1]")).body
    assert isinstance(body[1].rhs, EDictAccess)
    assert body[1].rhs.key.value == 1

def test_dict_assign():
    body = program_main(shrink_prog("k: int = 1\nd: dict[int, int] = {}\nd[k] = 5")).body
    stmt = body[2]
    assert isinstance(stmt, SAssign)
    assert isinstance(stmt.lhs, EDictAccess)

def test_dict_items_shrunk():
    body = program_main(shrink_prog("x: int = 1\ny: int = 2\nd = {x: y}")).body
    items = list(body[2].rhs.items)
    k, v = items[0]
    assert isinstance(k, EVar)
    assert isinstance(v, EVar)

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
