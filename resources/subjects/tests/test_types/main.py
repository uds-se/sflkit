import sys


def f(a: str, b: str):
    x = 2j
    y = 3j if b else 2j
    if a < b:
        c, d = a.encode(), b.encode()
        if c.startswith(b"t"):
            return b
        else:
            return d
    return None if x == y else x


f(sys.argv[1], sys.argv[2])
