import sys


def evaluate(args):
    for a in args:
        print(a)
        break


if __name__ == "__main__":
    evaluate(sys.argv[1:])
