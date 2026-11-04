"""Markdown table parsing for decks."""

import re
from pathlib import Path

_SPLIT = re.compile(r"(?<!\\)\|")


def cells(line: str) -> list[str]:
    parts = _SPLIT.split(line.strip().strip("|"))
    return [p.strip().replace("\\|", "|") for p in parts]


def find_table(path: Path, prefix: list[str]) -> tuple[list[str], list[dict[str, str]]] | None:
    """Header and rows of the first table whose header starts with prefix, or None."""
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        header = cells(line) if line.lstrip().startswith("|") else []
        if header[: len(prefix)] != prefix:
            continue
        rows, j = [], i + 2  # skip header + separator
        while j < len(lines) and lines[j].lstrip().startswith("|"):
            rows.append(dict(zip(header, cells(lines[j]))))
            j += 1
        return header, rows
    return None
