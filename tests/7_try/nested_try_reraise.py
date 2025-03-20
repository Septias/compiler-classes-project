try:
    try:
        raise Exception(42)
    except Exception as x:
        raise Exception(x + 1)
except Exception as x:
    print(x)
