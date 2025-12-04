class RGB:
    red: int
    green: int
    blue: int

    def intensity(self) -> int:
        return self.red + self.green + self.blue

    def addintensity(self, m: int) -> int:
        return (self.red + self.green + self.blue) + m

    def makemoreblue(self, m: int) -> None:
        self.blue = self.blue + m
        return None

    def evenmoreblue(self, g: int) -> None:
        self.blue = self.blue + g + g
        return None

    def makemoreblueandred(self, m: int) -> None:
        self.makemoreblue(m)
        self.red = self.red + m
        return None

    def changebutnoreturn(self, m: int) -> None:
        self.red = m

r = RGB(100, 24, 2)
print(r.intensity())
print(r.addintensity(10))
print(r.blue)
r.makemoreblue(5)
print(r.blue)
r.evenmoreblue(2)
print(r.blue)
r.makemoreblueandred(6)
print(r.blue)
print(r.red)
r.red = 15
print(r.red)

g = RGB(2, 2, 2)
g.changebutnoreturn(5)
print(g.red)