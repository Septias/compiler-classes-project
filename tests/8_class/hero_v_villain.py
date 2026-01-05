def cdiv(a: int, b: int) -> int:
    r = 0
    if b < 1:
        return a
    if a < 0:
        a = a - a - a
    while a >= b:
        a = a - b
        r = r + 1
    return r

class Entity:
    id: int
    hp: int
    direction: int # 0 - up, 1 - right, 2 - down, 3 - left
    steps_to_take: int
    pos: tuple[int,int]

    def calculate_defense(self, dmg: int) -> int:
        return dmg

class Player(Entity):
    mana: int

    def calculate_defense(self, dmg: int) -> int:
        if self.mana < 10:
            return dmg
        else:
            return cdiv(dmg, 2)

class Enemy(Entity):
    is_angry: bool

    def calculate_defense(self, dmg: int) -> int:
        return dmg - 5 # basic armor

class Boss(Enemy):
    shield_up: bool

    def calculate_defense(self, dmg: int) -> int:
        if self.shield_up:
            return 0
        return dmg - 10 # good armor

def simulate_round(e: Entity, dmg: int) -> None:
    actual_dmg = e.calculate_defense(dmg)
    e.hp = e.hp - actual_dmg
    if e.steps_to_take > 0:
        if e.direction == 0 and e.pos[1] > 0:
            e.pos = (e.pos[0], e.pos[1] - 1)
        if e.direction == 1:
            e.pos = (e.pos[0] + 1, e.pos[1])
        if e.direction == 2:
            e.pos = (e.pos[0], e.pos[1] + 1)
        if e.direction == 3 and e.pos[0] > 0:
            e.pos = (e.pos[0] - 1, e.pos[1])
        e.steps_to_take = e.steps_to_take - 1

p = Player(1, 100, 2, 5, (0, 0), 50)  # ID, HP, dir, steps, Pos, Mana
b = Boss(2, 200, 3, 3, (10, 10), True, True)
# player
print(p.hp)
print(p.direction)
print(p.steps_to_take)
print(p.pos[0])
print(p.pos[1])
print(p.mana)
# boss
print(b.hp)
print(b.direction)
print(b.steps_to_take)
print(b.pos[0])
print(b.pos[1])
#print(b.is_angry)
#print(b.shield_up)

player_dmg_output = 45
boss_dmg_output = 6
simulate_round(p, boss_dmg_output)
simulate_round(b, player_dmg_output)
# player
print(p.hp)
print(p.direction)
print(p.steps_to_take)
print(p.pos[0])
print(p.pos[1])
print(p.mana)
# boss
print(b.hp)
print(b.direction)
print(b.steps_to_take)
print(b.pos[0])
print(b.pos[1])
#print(b.is_angry)
#print(b.shield_up)
