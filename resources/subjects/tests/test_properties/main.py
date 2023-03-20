class T:
    def __init__(self):
        self.t = 0

    @property
    def d(self):
        self.t += 1
        return self.t


t = T()
assert t.d == 1
