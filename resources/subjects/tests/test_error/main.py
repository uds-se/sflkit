import sys


def f(x: int):
    if x < 0:
        raise ValueError("x must be non-negative")
    else:
        return x


def g(x: int):
    if x < 0:
        return -x
    else:
        return x


if __name__ == "__main__":
    x_ = int(sys.argv[1])
    g(x_)
    f(x_)
