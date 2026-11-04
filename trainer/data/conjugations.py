"""Read a conjugation table and read/write its stats.

Table columns: korean | english | tags | pos | rule | <form>... where every column
after `rule` is a form and `nan` marks a form that doesn't exist. One card per
(word, form). Stats are keyed by korean + form.
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from trainer.data import stats as store
from trainer.data.stats import MAX_BOX
from trainer.data.table import find_table
from trainer.data.vocab import Word

FIXED = ["korean", "english", "tags", "pos", "rule"]
NAN = "nan"
# Derived forms: (label, source column, old, new). Not stored in the table.
DERIVED = [("고 싶어해요", "고 싶어요", "싶어요", "싶어해요")]


@dataclass
class Card:
    korean: str
    english: str
    form: str
    target: str
    rule: str = ""
    pos: str = ""
    tags: list[str] = field(default_factory=list)
    ok: tuple[int, int] = (0, 0)  # (correct, attempts)
    box: int = 0
    last: str = ""

    @property
    def key(self) -> tuple[str, str]:
        return (self.korean, self.form)

    @property
    def score(self) -> int | None:
        """0-100: smoothed accuracy (80%) + box (20%). None if never tested."""
        if not self.ok[1]:
            return None
        c, n = self.ok
        return round(100 * (0.8 * (c + 1) / (n + 2) + 0.2 * self.box / MAX_BOX))

    def stats(self, direction: str) -> tuple[int, int]:
        return self.ok

    def ask(self, direction: str) -> str:
        return self.korean

    def expect(self, direction: str) -> str:
        return self.target


def load_table(path: Path) -> tuple[list[Card], list[str]]:
    """All cards, and the form names in column order (derived forms after their source)."""
    table = find_table(path, FIXED)
    if table is None:
        raise ValueError(f"{path}: no conjugation table (header '{' | '.join(FIXED)} | ...') found")
    header, rows = table
    forms = []
    for f in header[len(FIXED):]:
        forms.append(f)
        forms += [d[0] for d in DERIVED if d[1] == f]
    cards = []
    for c in rows:
        base = dict(korean=c["korean"], english=c["english"], rule=c["rule"], pos=c["pos"], tags=c["tags"].split())
        for f in header[len(FIXED):]:
            t = c.get(f, "")
            if not t or t == NAN:
                continue
            cards.append(Card(form=f, target=t, **base))
            for label, src, old, new in DERIVED:
                if src == f and old in t:
                    cards.append(Card(form=label, target=t.replace(old, new), **base))
    return cards, forms


def _key(korean: str, form: str) -> str:
    return f"{korean}\t{form}"


def _apply(c: Card, s: dict) -> None:
    c.ok = tuple(s.get("ok", (0, 0)))
    c.box = s.get("box", 0)
    c.last = s.get("last", "")


def load(table: Path, stats: Path) -> tuple[list[Card], list[str]]:
    cards, forms = load_table(table)
    saved = store.read(stats)
    for c in cards:
        if s := saved.get(_key(*c.key)):
            _apply(c, s)
    return cards, forms


def _update(stats: Path, key: tuple[str, str], fn) -> Card:
    saved = store.read(stats)
    c = Card(key[0], "", key[1], "")
    _apply(c, saved.get(_key(*key), {}))
    fn(c)
    saved[_key(*key)] = {"ok": list(c.ok), "box": c.box, "last": c.last}
    store.write(stats, saved)
    return c


def record(stats: Path, key: tuple[str, str], correct: bool) -> Card:
    def fn(c: Card) -> None:
        c.ok = (c.ok[0] + correct, c.ok[1] + 1)
        c.box = min(c.box + 1, MAX_BOX) if correct else 0
        c.last = date.today().isoformat()

    return _update(stats, key, fn)


def undo_miss(stats: Path, key: tuple[str, str], prev_box: int) -> Card:
    def fn(c: Card) -> None:
        c.ok = (c.ok[0] + 1, c.ok[1])
        c.box = min(prev_box + 1, MAX_BOX)

    return _update(stats, key, fn)


def summary(cards: list[Card], attr: str) -> list[dict]:
    """Accuracy grouped by `rule` or `form`, weakest first, untested last."""
    groups: dict[str, list[Card]] = {}
    for c in cards:
        groups.setdefault(getattr(c, attr), []).append(c)
    rows = []
    for name, cs in groups.items():
        right, n = sum(c.ok[0] for c in cs), sum(c.ok[1] for c in cs)
        rows.append({attr: name, "cards": len(cs), "correct": f"{right}/{n}" if n else "", "pct": round(100 * right / n) if n else None})
    return sorted(rows, key=lambda r: (r["pct"] is None, r["pct"] or 0))


def problems(words: list[Word], cards: list[Card]) -> list[str]:
    """Deck collisions: one row per Korean word in each table, and conjugation rows matching
    their vocab row. Stats, stars and learn grouping all rely on this."""
    out = [f"vocab: {k} has {n} rows" for k, n in Counter(w.korean for w in words).items() if n > 1]
    dup = {k for (k, _), n in Counter(c.key for c in cards).items() if n > 1}
    out += [f"conjugations: {k} has more than one row" for k in dup]
    vocab = {w.korean: w for w in words}
    for c in {c.korean: c for c in cards}.values():
        w = vocab.get(c.korean)
        if w is None:
            out.append(f"conjugations: {c.korean} isn't in vocab")
        elif (c.english, c.tags) != (w.english, w.tags):
            out.append(f"conjugations: {c.korean} is '{c.english}' {c.tags}, vocab has '{w.english}' {w.tags}")
    return out

