try:
    try:
        raise Exception(42)
    except Exception as x:
        print(0)
except Exception as x:
    print(1)
