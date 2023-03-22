class A:
    def __init__(self, b):  # defs: 2, uses: 1
        self.b = b

    def a(self, b):  # defs: 1, uses: 2
        return self.b + b


def a(b, c):  # defs: 2, uses: 0
    d = A(b)  # defs: 1, uses: 1
    for i in range(c):  # defs: 1, uses: 1
        d.b = d.a(b)  # defs: 1, uses: 1
    return d.b  # defs: 0, uses: 1


if a(0, 0):
    print("fallback")
elif a(4, 5) and a(1, 1):
    print("passed")
else:
    print("failed")

try:
    raise ValueError()
except ValueError:
    print("catch")
