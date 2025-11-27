class A:
    a: int

    def ab(self, ar: int) -> int:
        return self.a + ar
    
    def de(self, g: int) -> int:
        return self.a - g

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

ca = A(3)
print(ca.ab(2)) # 5
print(ca.de(1)) # 2

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