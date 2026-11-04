from pathlib import Path

import pytest

from trainer.data import conjugations, vocab

DECKS = Path(__file__).resolve().parents[1] / "decks"


@pytest.mark.parametrize("course", [d.name for d in DECKS.iterdir() if (d / "conjugations.md").exists()])
def test_no_deck_collisions(course):
    """One row per Korean word, and every conjugation row matches its vocab row."""
    words = vocab.load_deck(DECKS / course / "vocab.md")
    cards, _ = conjugations.load_table(DECKS / course / "conjugations.md")
    assert conjugations.problems(words, cards) == []
