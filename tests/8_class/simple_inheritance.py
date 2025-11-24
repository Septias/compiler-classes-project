class A:
    x: int

    def px(self) -> int:
        return self.x

class B(A):
    y: int

    def px(self) -> int:
        return self.x + self.x
    
    def py(self) -> int:
        return self.y

a = A(1)
print(a.px())
b = B(1, 3)
print(b.px())
print(b.py())