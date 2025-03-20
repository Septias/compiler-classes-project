print(0)
try:
    print(1)
    raise Exception(42)
    print(2)
except Exception as x:
    print(x)
print(3)
