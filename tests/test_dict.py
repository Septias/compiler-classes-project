import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pass_0_1_parser import parse
from type_checker import type_check, TypeError
from semantics import eval_prog, VDict
from io import StringIO
import contextlib

def run(src):
    p = parse(src)
    type_check(p)
    buf = StringIO()
    with contextlib.redirect_stdout(buf):
        eval_prog(p)
    return buf.getvalue().strip()

def expect_type_error(src):
    try:
        p = parse(src)
        type_check(p)
        raise AssertionError("Expected TypeError but none was raised")
    except TypeError:
        pass

# --- basic ---

def test_literal_and_get():
    assert run("d: dict[int, int] = {1: 10, 2: 20}\nprint(d[1])") == "10"

def test_set_and_get():
    assert run("""
d: dict[int, int] = {}
d[1] = 42
print(d[1])
""") == "42"

def test_overwrite():
    assert run("""
d: dict[int, int] = {1: 10}
d[1] = 99
print(d[1])
""") == "99"

def test_multiple_keys():
    assert run("""
d: dict[int, int] = {1: 10, 2: 20, 3: 30}
print(d[2])
print(d[3])
""") == "20\n30"

def test_variable_key():
    assert run("""
d: dict[int, int] = {5: 50}
k = 5
print(d[k])
""") == "50"

# --- types ---

def test_bool_value():
    assert run("""
d: dict[int, bool] = {1: True}
print(d[1])
""") == "True"

def test_infer_key_type_from_literal():
    assert run("""
d = {10: 1, 20: 2}
print(d[10])
""") == "1"

# --- type errors ---

def test_wrong_value_type():
    expect_type_error("""
d: dict[int, int] = {1: True}
""")

def test_access_on_non_dict():
    expect_type_error("""
x = 5
y = x[1]
""")

def test_empty_dict_no_annotation():
    expect_type_error("d = {}")

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
