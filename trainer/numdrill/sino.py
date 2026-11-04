"""Sino-Korean numbers: integer -> Hangul reading, up to 99,999,999."""

MAX = 99_999_999
_DIGITS = "영일이삼사오육칠팔구"


def _below_10000(n: int) -> str:
    out = ""
    for d, unit in ((n // 1000 % 10, "천"), (n // 100 % 10, "백"), (n // 10 % 10, "십"), (n % 10, "")):
        if d:
            out += ("" if d == 1 and unit else _DIGITS[d]) + unit  # 십, not 일십
    return out


def sino(n: int) -> str:
    if n == 0:
        return "영"
    hi, lo = divmod(n, 10_000)
    out = ""
    if hi:
        out = ("" if hi == 1 else _below_10000(hi)) + "만"  # 만, not 일만
    return out + _below_10000(lo)

