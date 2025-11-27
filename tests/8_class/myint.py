class MyInt(int):
    value: int

    def times(self, t: int) -> int:
        a = 0
        while t > 0:
            a = a + self.value
            t = t - 1
        return a

g = MyInt(5)
print(g.times(2))
print(g.value)
print(g.times(5))
print(g + 5)