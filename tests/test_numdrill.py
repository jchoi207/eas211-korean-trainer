import random

import pytest

from trainer.numdrill.questions import _MAKERS, Q, en_num, make, native, span, usable
from trainer.numdrill.sino import sino


@pytest.mark.parametrize(
    "n, ko",
    {
        0: "영", 1: "일", 10: "십", 11: "십일", 16: "십육", 20: "이십", 99: "구십구", 100: "백", 101: "백일",
        1234: "천이백삼십사", 10000: "만", 10001: "만일", 120000: "십이만", 99_999_999: "구천구백구십구만구천구백구십구",
    }.items(),
)
def test_sino(n, ko):
    assert sino(n) == ko


def test_native():
    assert native(1) == "하나" and native(20) == "스물" and native(99) == "아흔아홉"
    assert native(1, True) == "한" and native(20, True) == "스무" and native(21, True) == "스물한"
    assert native(24, True) == "스물네" and native(10, True) == "열" and native(12, True) == "열두"


def test_en_num():
    assert en_num(2) == "two" and en_num(21) == "twenty-one" and en_num(40) == "forty"


def test_span():
    assert span("sino", 0, 100) == (0, 100) and span("native", 0, 200) == (1, 99) and span("native", 100, 200) is None


@pytest.mark.parametrize("cat", list(_MAKERS))
def test_category_accepts_its_own_answer(cat):
    for _ in range(300):
        q = make([cat], 0, 100)
        assert q.ko_ok(q.ko) and q.en_ok(q.prompt), (cat, q)


def test_alternate_readings():
    random.seed(0)
    q = Q("3:30 p.m.", "오후 세 시 반", ("3:30 p.m.", "3:30pm"), ("오후 세 시 삼십 분",))
    assert q.ko_ok("오후 세 시 삼십 분") and q.ko_ok("오후세시반") and q.en_ok("3:30 PM")
    p = Q("010-123-4567", "영일영 일이삼 사오육칠", ("010-123-4567",), gong=True)
    assert p.ko_ok("공일공 일이삼 사오육칠")


def test_native_tens():
    assert {make(["native"], 100, 200, tens=True).ko for _ in range(300)} == {"열", "스물", "서른", "마흔", "쉰", "예순", "일흔", "여든", "아흔"}


def test_multiple_categories():
    kinds = {make(["native", "phone"], 0, 100).gong for _ in range(200)}
    assert kinds == {True, False}  # both categories get drawn
    assert usable(["sino", "native"], 100, 200) == ["sino"]
    assert "native" not in usable([], 100, 200) and "phone" in usable([], 100, 200)
