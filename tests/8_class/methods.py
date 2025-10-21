class RGB:
    red: int
    green: int
    blue: int

    def intensity(self) -> int:
        return self.red + self.green + self.blue

    def addintensity(self, m: int) -> int:
        return (self.red + self.green + self.blue) + m

r = RGB(100, 24, 2)
print(r.blue + r.red + r.green)
print(r.intensity())
print(r.addintensity(10))
print(r.blue)