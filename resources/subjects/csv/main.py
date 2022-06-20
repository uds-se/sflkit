import sys

import csv2


def main(arg):
    with open(arg) as f:
        r = csv2.DictReader(f)
        for row in r:
            print(row)


if __name__ == '__main__':
    main(sys.argv[1])
