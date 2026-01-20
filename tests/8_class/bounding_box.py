class Point:
    x: int
    y: int

class Rect:
    anchor: Point
    w: int
    h: int

def is_inside(r: Rect, p: Point) -> bool:
    is_in_x = (p.x >= r.anchor.x) and (p.x <= r.anchor.x + r.w)
    is_in_y = (p.y >= r.anchor.y) and (p.y <= r.anchor.y + r.h)
    return is_in_x and is_in_y

def print_if_true(b: bool):
    if b:
        print(1)
    else:
        print(0)

def test_1():
    bb = Rect(Point(10, 10), 50, 50)
    p = Point(20, 30)
    print_if_true(is_inside(bb, p))
    p = Point(20, 70)
    print_if_true(is_inside(bb, p))

test_1()