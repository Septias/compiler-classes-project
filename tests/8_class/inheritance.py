class Point2d:
    x: int
    y: int

    def magnitude (self) -> int:
        return self.x + self.y


class Point3d(Point2d):
    z: int

    def magnitude (self) -> int:
        return self.x + self.y + self.z

def get_x (p: Point2d) -> int:
    return p.x


p3 = Point3d(1, 2, 3)
print(get_x(p3))
print(p3.magnitude())

