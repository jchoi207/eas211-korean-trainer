"""Typed-answer matching."""

import re
import unicodedata

_HANGUL = re.compile(r"[가-힣ㄱ-ㆎ]")


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFC", s).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s.rstrip("?.!").strip()


def accepted(target: str) -> set[str]:
    """All answer forms accepted for a target string."""
    forms = {target, re.sub(r"\([^)]*\)", "", target)}
    forms |= set(re.findall(r"\(([^)]*)\)", target))
    forms |= {p for f in list(forms) for p in re.split(r"[/,;]", f)}
    forms |= {f.replace("(", "").replace(")", "") for f in list(forms)}
    out = {normalize(f) for f in forms} - {""}
    for prefix in ("to ", "please "):  # "to be glad" -> "be glad", "please sit down" -> "sit down"
        out |= {f[len(prefix):] for f in out if f.startswith(prefix)}
    return out


def _squash(s: str) -> str:
    return s.replace(" ", "")


def check(answer: str, target: str) -> bool:
    a = normalize(answer)
    if not a:
        return False
    forms = accepted(target)
    if _HANGUL.search(target):
        return _squash(a) in {_squash(f) for f in forms}
    return a in forms or any(a.startswith(p) and a[len(p):] in forms for p in ("to ", "please "))


if __name__ == "__main__":
    assert check("be glad", "To be glad (to meet)")
    assert check("to be glad", "To be glad (to meet)")
    assert check("to be glad to meet", "To be glad (to meet)")
    assert check("저", "저 (나)") and check("나", "저 (나)")
    assert check("이름이뭐예요", "이름이 뭐예요?")
    assert check("person", "Person/people") and check("people", "Person/people")
    assert check("we", "We, our (my)") and check("my", "We, our (my)")
    assert check("the philippines", "The Philippines")
    assert check("mr", "Mr./Ms. (first name)") and check("mr./ms.", "Mr./Ms. (first name)")
    assert check("sit down", "please sit down") and check("please sit down", "sit down")
    assert not check("", "USA") and not check("canada", "USA")
    print("ok")
