"""Numbers study questions: each category makes a prompt (digits or English) and its Korean reading."""

import random
import re
from dataclasses import dataclass

from checking import check
from sino import MAX as SINO_MAX, sino

CATEGORIES = {
    "sino": "Sino-Korean",
    "native": "Native",
    "count": "Counting",
    "time": "Time",
    "age": "Age",
    "date": "Dates",
    "price": "Price",
    "phone": "Phone",
    "mixed": "Mixed",
}
RANGED = {"sino", "native", "count", "age", "mixed"}  # categories that use the From/To range

_ONES = ["", "하나", "둘", "셋", "넷", "다섯", "여섯", "일곱", "여덟", "아홉"]
_TENS = ["", "열", "스물", "서른", "마흔", "쉰", "예순", "일흔", "여든", "아흔"]
_BEFORE_UNIT = {1: "한", 2: "두", 3: "세", 4: "네"}
_DIGITS = "영일이삼사오육칠팔구"

# counting unit, singular, plural
UNITS = [
    ("명", "person", "people"),
    ("개", "thing", "things"),
    ("병", "bottle", "bottles"),
    ("장", "paper", "papers"),
    ("마리", "animal", "animals"),
    ("권", "book", "books"),
    ("대", "car", "cars"),
    ("잔", "drink", "drinks"),
    ("벌", "piece of clothing", "pieces of clothing"),
]
_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_EN_ONES = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
_EN_TENS = "twenty thirty forty fifty sixty seventy eighty ninety".split()


@dataclass
class Q:
    prompt: str  # shown as digits or English
    ko: str
    en: tuple[str, ...]  # accepted typed answers for the prompt side
    alts: tuple[str, ...] = ()  # other accepted Korean readings
    gong: bool = False  # 공 counts as 영 (phone numbers)

    def ko_ok(self, answer: str) -> bool:
        if self.gong:
            squash = lambda s: s.replace(" ", "").replace("공", "영")
            return squash(answer) == squash(self.ko)
        return any(check(answer, k) for k in (self.ko, *self.alts))

    def en_ok(self, answer: str) -> bool:
        return _en_norm(answer) in {_en_norm(e) for e in self.en}


def _en_norm(s: str) -> str:
    return re.sub(r"[\s.,$₩]", "", s.lower())


def native(n: int, before_unit: bool = False) -> str:
    """1 to 99. Before a counting unit 1-4 become 한 두 세 네 and 20 becomes 스무."""
    if before_unit and n == 20:
        return "스무"
    tens, ones = divmod(n, 10)
    return _TENS[tens] + (_BEFORE_UNIT[ones] if before_unit and ones in _BEFORE_UNIT else _ONES[ones])


def en_num(n: int) -> str:
    if n < 20:
        return _EN_ONES[n - 1]
    tens, ones = divmod(n, 10)
    return _EN_TENS[tens - 2] + (f"-{_EN_ONES[ones - 1]}" if ones else "")


def span(cat: str, lo: int, hi: int) -> tuple[int, int] | None:
    """The part of the From/To range a category can use, or None if nothing is left."""
    if cat == "sino":
        return (lo, min(hi, SINO_MAX)) if lo <= min(hi, SINO_MAX) else None
    lo, hi = max(lo, 1), min(hi, 99)
    return (lo, hi) if lo <= hi else None


def _sino(lo: int, hi: int) -> Q:
    n = random.randint(lo, hi)
    return Q(f"{n:,}", "영/공" if n == 0 else sino(n), (str(n),))


def _native(lo: int, hi: int) -> Q:
    n = random.randint(lo, hi)
    return Q(f"{n}", native(n), (str(n),))


def _count(lo: int, hi: int) -> Q:
    n = random.randint(lo, hi)
    unit, one, many = random.choice(UNITS)
    noun = one if n == 1 else many
    return Q(f"{en_num(n)} {noun}", f"{native(n, True)} {unit}", (f"{n} {noun}", f"{en_num(n)} {noun}"))


def _age(lo: int, hi: int) -> Q:
    n = random.randint(lo, hi)
    en = f"{n} year{'' if n == 1 else 's'} old"
    return Q(en, f"{native(n, True)} 살", (en, str(n), f"{en_num(n)} year{'' if n == 1 else 's'} old"))


def _time(lo: int, hi: int) -> Q:
    h = random.randint(1, 12)
    m = random.choice(range(0, 60, 5)) if random.random() < 0.6 else random.randint(0, 59)
    pm = random.random() < 0.5
    en = f"{h}:{m:02d} {'p.m.' if pm else 'a.m.'}"
    ko = f"{'오후' if pm else '오전'} {native(h, True)} 시"
    alts = ()
    if m == 30:
        alts = (f"{ko} 삼십 분",)
        ko += " 반"
    elif m:
        ko += f" {sino(m)} 분"
    return Q(en, ko, (en, f"{h}:{m:02d}{'pm' if pm else 'am'}"), alts)


def _date(lo: int, hi: int) -> Q:
    m = random.randint(1, 12)
    d = random.randint(1, _DAYS[m - 1])
    month = {6: "유월", 10: "시월"}.get(m, f"{sino(m)}월")
    en = f"{_MONTHS[m - 1]} {d}"
    return Q(en, f"{month} {sino(d)}일", (en, f"{_MONTHS[m - 1][:3]} {d}", f"{m}/{d}"))


def _price(lo: int, hi: int) -> Q:
    if random.random() < 0.5:
        n = random.randint(1, 999)
        return Q(f"${n}", f"{sino(n)} 불", (f"${n}", f"{n} dollars"), (f"{sino(n)} 달러",))
    n = random.randint(1, 999) * 100
    return Q(f"₩{n:,}", f"{sino(n)} 원", (f"₩{n:,}", f"{n} won"))


def _phone(lo: int, hi: int) -> Q:
    groups = ["".join(random.choices("0123456789", k=k)) for k in (3, 3, 4)]
    ko = " ".join("".join(_DIGITS[int(c)] for c in g) for g in groups)
    return Q("-".join(groups), ko, ("-".join(groups), "".join(groups)), gong=True)


_MAKERS = {
    "sino": _sino, "native": _native, "count": _count, "time": _time,
    "age": _age, "date": _date, "price": _price, "phone": _phone,
}


def make(cat: str, lo: int, hi: int) -> Q:
    if cat == "mixed":
        cat = random.choice(list(_MAKERS))
    lo, hi = span(cat, lo, hi) or (1, 99)
    return _MAKERS[cat](lo, hi)


if __name__ == "__main__":
    assert native(1) == "하나" and native(20) == "스물" and native(99) == "아흔아홉"
    assert native(1, True) == "한" and native(20, True) == "스무" and native(21, True) == "스물한"
    assert native(24, True) == "스물네" and native(10, True) == "열" and native(12, True) == "열두"
    assert en_num(2) == "two" and en_num(21) == "twenty-one" and en_num(40) == "forty"
    assert span("sino", 0, 100) == (0, 100) and span("native", 0, 200) == (1, 99) and span("native", 100, 200) is None
    for _ in range(300):  # every category runs, and its own answer is accepted both ways
        for cat in _MAKERS:
            q = make(cat, 0, 100)
            assert q.ko_ok(q.ko) and q.en_ok(q.prompt), (cat, q)
    random.seed(0)
    q = Q("3:30 p.m.", "오후 세 시 반", ("3:30 p.m.", "3:30pm"), ("오후 세 시 삼십 분",))
    assert q.ko_ok("오후 세 시 삼십 분") and q.ko_ok("오후세시반") and q.en_ok("3:30 PM")
    p = Q("010-123-4567", "영일영 일이삼 사오육칠", ("010-123-4567",), gong=True)
    assert p.ko_ok("공일공 일이삼 사오육칠")
    print("ok")
