class Point2d:
    x: int
    y: int

    def magnitude (self) -> int:
        return self.x + self.y


class Point3d(Point2d):
    z: int

    def magnitude (self) -> int:
        return self.x + self.y + self.z

class SomethingElse:
    a: int

def get_x (p: Point2d) -> int:
    return p.x

p2 = Point2d(9, 12)
print(get_x(p2))
print(p2.magnitude())
p3 = Point3d(1, 2, 3)
print(get_x(p3))
print(p3.magnitude())
se = SomethingElse(1)
print(get_x(se))
se.magnitude()

