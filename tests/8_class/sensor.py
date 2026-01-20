class Sensor:
    raw_value: int

    def read(self) -> int:
        return self.raw_value

class SmartSensor(Sensor):
    offset: int
    multiplier: int

    def read(self) -> int:
        return pmul(self.raw_value + self.offset, self.multiplier)

def is_safe(sensor: Sensor, alerts: Callable[[int], bool]) -> bool:
    if not alerts(sensor.read()):
        return True
    else:
        return False

def pmul(a: int, b: int) -> int:
    if a < 0 or b < 0:
        raise Exception(1)
    r = 0
    while b > 0:
        r = r + a
        b = b - 1
    return r

def pdiv(a: int, b: int) -> int:
    if a < 0 or b < 0:
        raise Exception(1)
    r = 0
    while a >= b:
        a = a - b
        r = r + 1
    return r

def print_if_true(b: bool):
    if b:
        print(1)
    else:
        print(0)

def test():
    sensor1 = Sensor(120)
    print(sensor1.read())
    sensor2 = SmartSensor(110, 5, 2)
    print(sensor2.read())
    safe_range = (150, 250)
    alert: Callable[[int], bool] = lambda x: x < safe_range[0] or x > safe_range[1]
    print_if_true(is_safe(sensor1, alert))
    print_if_true(is_safe(sensor2, alert))

test()