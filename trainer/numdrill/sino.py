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


if __name__ == "__main__":
    for n, ko in {
        0: "영", 1: "일", 10: "십", 11: "십일", 16: "십육", 20: "이십", 99: "구십구", 100: "백", 101: "백일",
        1234: "천이백삼십사", 10000: "만", 10001: "만일", 120000: "십이만", 99_999_999: "구천구백구십구만구천구백구십구",
    }.items():
        assert sino(n) == ko, (n, sino(n), ko)
    print("ok")
