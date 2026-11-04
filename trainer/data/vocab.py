"""Read a deck (markdown word table) and read/write its stats (JSON, not tracked by git).

The app never writes the deck. Stats are keyed by (korean, english), so editing a
word's tags or notes keeps its history, and renaming it starts fresh.
"""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from trainer.data import stats as store
from trainer.data.stats import MAX_BOX
from trainer.data.table import find_table

DECK_COLUMNS = ["korean", "english", "tags", "notes"]
COLUMNS = DECK_COLUMNS + ["ko→en", "en→ko", "box", "score", "last"]  # shown in the word table


@dataclass
class Word:
    korean: str
    english: str
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    ko_en: tuple[int, int] = (0, 0)  # (correct, attempts)
    en_ko: tuple[int, int] = (0, 0)
    box: int = 0
    last: str = ""

    @property
    def key(self) -> tuple[str, str]:
        return (self.korean, self.english)

    @property
    def score(self) -> int | None:
        """0-100 mastery from both directions and the box. None if never tested.

        Accuracy per direction is smoothed toward 50% ((c+1)/(n+2)), so a single
        right answer isn't mastery, and an untested direction counts as 50%.
        """
        if not (self.ko_en[1] or self.en_ko[1]):
            return None
        acc = [(c + 1) / (n + 2) for c, n in (self.ko_en, self.en_ko)]
        return round(100 * (0.4 * acc[0] + 0.4 * acc[1] + 0.2 * self.box / MAX_BOX))

    def stats(self, direction: str) -> tuple[int, int]:
        if direction == "ko→en":
            return self.ko_en
        if direction == "en→ko":
            return self.en_ko
        return (self.ko_en[0] + self.en_ko[0], self.ko_en[1] + self.en_ko[1])

    def ask(self, direction: str) -> str:
        return self.korean if direction == "ko→en" else self.english

    def expect(self, direction: str) -> str:
        return self.english if direction == "ko→en" else self.korean


# deck


def load_deck(path: Path) -> list[Word]:
    """Words from the first table whose header starts korean | english."""
    table = find_table(path, ["korean", "english"])
    if table is None:
        raise ValueError(f"{path}: no vocab table (header 'korean | english | ...') found")
    return [Word(c.get("korean", ""), c.get("english", ""), c.get("tags", "").split(), c.get("notes", "")) for c in table[1]]


# stats


def _key(korean: str, english: str) -> str:
    return f"{korean}\t{english}"


def _apply(w: Word, s: dict) -> None:
    w.ko_en = tuple(s.get("ko_en", (0, 0)))
    w.en_ko = tuple(s.get("en_ko", (0, 0)))
    w.box = s.get("box", 0)
    w.last = s.get("last", "")


def _dump(w: Word) -> dict:
    return {"ko_en": list(w.ko_en), "en_ko": list(w.en_ko), "box": w.box, "last": w.last}


def load(deck: Path, stats: Path) -> list[Word]:
    """Deck words with their stats attached."""
    words = load_deck(deck)
    saved = store.read(stats)
    for w in words:
        if s := saved.get(_key(*w.key)):
            _apply(w, s)
    return words


def _update(stats: Path, key: tuple[str, str], fn) -> Word:
    """Apply fn to one word's stats. Re-reads the file first so other sessions' writes survive."""
    saved = store.read(stats)
    w = Word(*key)
    _apply(w, saved.get(_key(*key), {}))
    fn(w)
    saved[_key(*key)] = _dump(w)
    store.write(stats, saved)
    return w


def _attr(direction: str) -> str:
    return "ko_en" if direction == "ko→en" else "en_ko"


def record(stats: Path, key: tuple[str, str], direction: str, correct: bool) -> Word:
    def fn(w: Word) -> None:
        c, n = getattr(w, _attr(direction))
        setattr(w, _attr(direction), (c + correct, n + 1))
        w.box = min(w.box + 1, MAX_BOX) if correct else 0
        w.last = date.today().isoformat()

    return _update(stats, key, fn)


def undo_miss(stats: Path, key: tuple[str, str], direction: str, prev_box: int) -> Word:
    """Turn the last recorded miss into a hit ("I was right")."""
    def fn(w: Word) -> None:
        c, n = getattr(w, _attr(direction))
        setattr(w, _attr(direction), (c + 1, n))
        w.box = min(prev_box + 1, MAX_BOX)

    return _update(stats, key, fn)
