class A:
    l: bool
    m: int
    a: int

class B:
    g: int
    b: bool

    def influence_other(self, other: A) -> None:
        if self.b == False:
            other.a = 0

def test():
    a = A(False, 2, 3)
    l = A(True, 20, 5)
    b = B(12, False)
    c = B(17, True)
    b.influence_other(a)
    c.influence_other(l)
    print(a.a)
    print(l.a)

test()