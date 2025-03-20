def f(x: int) -> int:
    return g(x + 1)

def g(x: int) -> int:
    if x == 0:
        return 0
    else:
        raise Exception(42)

print(f(-1))
try:
    print(f(1))
except Exception as x:
    print(x)
