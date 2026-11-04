"""Where decks and stats live."""

from dataclasses import dataclass
from pathlib import Path

from trainer.data.stats import stats_path

ROOT = Path(__file__).resolve().parent.parent
DECKS = ROOT / "decks"
STATS = ROOT / "stats"
DEFAULT_DECK = DECKS / "eas211" / "vocab.md"


@dataclass(frozen=True)
class Paths:
    deck: Path
    stats: Path
    conj: Path  # optional, enables Study: Conjugations
    conj_stats: Path
    starred: Path

    @classmethod
    def for_deck(cls, deck: Path) -> "Paths":
        deck = deck.resolve()
        conj = deck.parent / "conjugations.md"
        stats = stats_path(deck, DECKS, STATS)
        return cls(deck, stats, conj, stats_path(conj, DECKS, STATS), stats.parent / "starred.json")
