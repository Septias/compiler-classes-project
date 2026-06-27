import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pass_0_1_parser import parse
from ast_1_python import EDict, EDictAccess, SAssign, pretty_expr, pretty_stmt
from types_ import TDict, TInt
from identifier import Id

def test_dict_literal():
    p = parse("d = {1: 2, 3: 4}")
    stmt = p.main_body[0]
    assert isinstance(stmt, SAssign)
    assert isinstance(stmt.rhs, EDict)
    items = list(stmt.rhs.items)
    assert len(items) == 2

def test_dict_access():
    p = parse("x = d[k]")
    stmt = p.main_body[0]
    assert isinstance(stmt, SAssign)
    assert isinstance(stmt.rhs, EDictAccess)

def test_dict_subscript_assign():
    p = parse("d[1] = 99")
    stmt = p.main_body[0]
    assert isinstance(stmt, SAssign)
    assert isinstance(stmt.lhs, EDictAccess)

def test_dict_type_annotation():
    p = parse("d: dict[int, int] = {}")
    stmt = p.main_body[0]
    assert isinstance(stmt, SAssign)
    assert isinstance(stmt.ty, TDict)
    assert isinstance(stmt.ty.key_ty, TInt)
    assert isinstance(stmt.ty.val_ty, TInt)

def test_tuple_access_still_works():
    p = parse("x = t[0]")
    from ast_1_python import ETupleAccess
    stmt = p.main_body[0]
    assert isinstance(stmt.rhs, ETupleAccess)
    assert stmt.rhs.index == 0

def test_pretty_dict_literal():
    p = parse("d = {1: 2}")
    assert pretty_stmt(p.main_body[0]) == "d = {1: 2}"

def test_pretty_dict_access():
    p = parse("x = d[k]")
    assert pretty_stmt(p.main_body[0]) == "x = d[k]"

def test_pretty_dict_assign():
    p = parse("d[1] = 99")
    assert pretty_stmt(p.main_body[0]) == "d[1] = 99"

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
