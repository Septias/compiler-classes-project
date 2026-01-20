class BankAccount:
    balance: int
    taxcode: Callable[[int], int]

    def deposit(self, i: int) -> None:
        self.balance = self.balance + i

    def take_tax(self) -> None:
        # self.balance does not know of self!
        tax = self.taxcode(self.balance)
        self.balance = self.balance - tax

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

def test():
    our_taxes: Callable[[int], int] = lambda money: pdiv(money, 5) if money < 1000 else pdiv(money, 2)
    professor_account = BankAccount(5000, our_taxes)
    student_account = BankAccount(20, our_taxes)
    student_account.deposit(450) # total 470
    # Tax season
    professor_account.take_tax() # takes 2500 leaving 2500
    student_account.take_tax() # takes 94 leaving 376
    print(professor_account.balance)
    print(student_account.balance)

test()