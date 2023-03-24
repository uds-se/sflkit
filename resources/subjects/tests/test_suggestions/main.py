import sys


def middle(x, y, z):
    m = z
    if y < z:
        if x < y:
            m = y
        elif x < z:
            m = y  # bug
    else:
        if x > y:
            m = y
        elif x > z:
            m = x
    return m


try:
    middle(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
except IndexError:
    pass
