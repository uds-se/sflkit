import sys

i = 0
for a in sys.argv[1]:
    i += ord(a)

while i < 100:
    i += 1
