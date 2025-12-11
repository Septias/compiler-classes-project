class A:
    a: int

    def ab(self, ar: int) -> int:
        return self.a + ar
    
    def de(self, g: int) -> int:
        return self.a - g
    
    def assign_a(self, new_a: int) -> None:
        self.a = new_a

class B(A):
    b: int
    def gu(self) -> int:
        return self.a + self.b
    
    def ab(self, ar: int) -> int:
        return self.a + self.b + ar

class C(B):
    def nt(self) -> int:
        return self.a - self.b

    def ab(self, ar: int) -> int:
        return self.a + self.b + ar + ar
    
    def lamtest(self, g: int) -> int:
        x = self.a
        y = 10
        f: Callable[[int], int] = lambda z: x + y + z
        return f(g)
    
    def lamassign(self, g: int) -> None:
        x = 5
        y = 10
        f: Callable[[int], int] = lambda z: x + y + z
        self.a = f(g)

class F(A):
    f: Callable[[int], int]

    def apply_f(self) -> int:
        return self.f(self.a)

ca = A(3)
print(ca.ab(2)) # 5
print(ca.de(1)) # 2
ca.assign_a(5)
print(ca.a) # 5

cb = B(2, 3)
print(cb.ab(2)) # 7
print(cb.de(1)) # 1 
print(cb.gu()) # 5
cb.b = 12
print(cb.b) # 12
print(cb.gu()) #14

cc = C(6, 8)
print(cc.ab(4)) # 22
print(cc.nt()) # -2
print(cc.gu()) # 14
print(cc.de(1)) # 5
cc.a = 12
print(cc.gu()) # 20

l = C(1, 2)
print(l.lamtest(1)) # 12
l.lamassign(12)
print(l.a) # 27

double_it: Callable[[int], int] = lambda z: z + z
f = F(2, double_it)
print(f.apply_f()) # 4