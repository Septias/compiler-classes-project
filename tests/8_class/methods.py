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

r = RGB(100, 24, 2)
print(r.intensity())
print(r.addintensity(10))
print(r.blue)
r.makemoreblue(5)
print(r.blue)