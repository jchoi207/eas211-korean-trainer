"""Read a deck (markdown word table) and read/write its stats (JSON, not tracked by git).

The app never writes the deck. Stats are keyed by (korean, english), so editing a
word's tags or notes keeps its history, and renaming it starts fresh.
"""

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

DECK_COLUMNS = ["korean", "english", "tags", "notes"]
COLUMNS = DECK_COLUMNS + ["ko→en", "en→ko", "box", "score", "last"]  # shown in the word table
MAX_BOX = 5
_SPLIT = re.compile(r"(?<!\\)\|")


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


def fmt_ratio(r: tuple[int, int]) -> str:
    return f"{r[0]}/{r[1]}" if r[1] else ""


# deck


def _cells(line: str) -> list[str]:
    parts = _SPLIT.split(line.strip().strip("|"))
    return [p.strip().replace("\\|", "|") for p in parts]


def load_deck(path: Path) -> list[Word]:
    """Words from the first table whose header starts korean | english."""
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        header = _cells(line) if line.lstrip().startswith("|") else []
        if header[:2] != ["korean", "english"]:
            continue
        words, j = [], i + 2  # skip header + separator
        while j < len(lines) and lines[j].lstrip().startswith("|"):
            c = dict(zip(header, _cells(lines[j])))
            words.append(Word(c.get("korean", ""), c.get("english", ""), c.get("tags", "").split(), c.get("notes", "")))
            j += 1
        return words
    raise ValueError(f"{path}: no vocab table (header 'korean | english | ...') found")


# stats


def stats_path(deck: Path, decks_dir: Path, stats_dir: Path) -> Path:
    """decks/eas211/vocab.md -> stats/eas211/vocab.json. Decks elsewhere -> stats/<name>.json."""
    try:
        rel = deck.resolve().relative_to(decks_dir.resolve())
    except ValueError:
        rel = Path(deck.name)
    return stats_dir / rel.with_suffix(".json")


def _key(korean: str, english: str) -> str:
    return f"{korean}\t{english}"


def _read_stats(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_stats(path: Path, stats: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".stats-", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


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
    saved = _read_stats(stats)
    for w in words:
        if s := saved.get(_key(*w.key)):
            _apply(w, s)
    return words


def _update(stats: Path, key: tuple[str, str], fn) -> Word:
    """Apply fn to one word's stats. Re-reads the file first so other sessions' writes survive."""
    saved = _read_stats(stats)
    w = Word(*key)
    _apply(w, saved.get(_key(*key), {}))
    fn(w)
    saved[_key(*key)] = _dump(w)
    _write_stats(stats, saved)
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
