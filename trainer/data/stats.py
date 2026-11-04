"""Stats files (JSON, not tracked by git) and starred words. Shared by the vocab and conjugation decks."""

import json
import os
import tempfile
from pathlib import Path

MAX_BOX = 5


def fmt_ratio(r: tuple[int, int]) -> str:
    return f"{r[0]}/{r[1]}" if r[1] else ""


def stats_path(deck: Path, decks_dir: Path, stats_dir: Path) -> Path:
    """decks/eas211/vocab.md -> stats/eas211/vocab.json. Decks elsewhere -> stats/<name>.json."""
    try:
        rel = deck.resolve().relative_to(decks_dir.resolve())
    except ValueError:
        rel = Path(deck.name)
    return stats_dir / rel.with_suffix(".json")


def read(path: Path) -> dict | list:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, stats: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".stats-", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


# stars: per Korean word, shared by its vocab rows and its conjugation cards


def load_starred(path: Path) -> set[str]:
    return set(read(path))


def toggle_star(path: Path, korean: str) -> set[str]:
    """Star or unstar a word. Re-reads the file first so other sessions' writes survive."""
    starred = load_starred(path) ^ {korean}
    write(path, sorted(starred))
    return starred
