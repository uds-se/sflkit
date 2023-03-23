import __future__
from string import digits

print(__future__.print_function)
print(digits)


class A:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def foo(x, y):
        return -x + y


async def bar(x, y, z):
    return x + y + z


t = (1, 2, 3)
n = bar(*t)
o = 1

with A() as a:
    a.foo(n, t[o])

async with A() as a:
    a.foo(0, 1)

while True:
    break

for i in range(1):
    continue

for i in range(1):
    pass

del a
global n


def baz():
    x = 1

    def f():
        nonlocal x
        x += 1

    f()
    return x


def foo():
    raise ValueError()


try:
    foo()
except ValueError:
    pass


m: int
m: int = 1
m += 1

if not False or m:
    print(m)
