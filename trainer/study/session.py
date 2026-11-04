"""Study session: word selection, ordering, and requeueing misses.

Works on vocab Words and conjugation Cards alike: both have key, tags, box, last,
stats(direction), ask(direction) and expect(direction).
"""

import random
from datetime import date

from vocab_io import MAX_BOX, Word

REQUEUE_GAP = 3  # a missed word comes back this many cards later


def select(words: list[Word], tags: set[str]) -> list[Word]:
    """Words carrying any of the tags (union). No tags = all words."""
    return [w for w in words if not tags or tags & set(w.tags)]


def worst(words: list[Word], n: int, direction: str) -> list[Word]:
    """The n words with the worst record in this direction. Unseen words rank last."""
    def rank(w: Word):
        c, a = w.stats(direction)
        miss_rate = (a - c + 1) / (a + 2)  # smoothed so 0/1 isn't worse than 3/10
        return (a == 0, -miss_rate, w.box, w.last)

    return sorted(words, key=rank)[:n]


def _weight(w: Word) -> float:
    days = (date.today() - date.fromisoformat(w.last)).days if w.last else 30
    return (MAX_BOX + 1 - w.box) * (1 + min(days, 30) / 7)


def weighted_order(words: list[Word]) -> list[Word]:
    """Shuffle, but low-box and long-unseen words tend to come first."""
    return sorted(words, key=lambda w: random.random() ** (1 / _weight(w)), reverse=True)


class Session:
    def __init__(self, words: list[Word], direction: str):
        self.direction = direction  # "ko→en" | "en→ko" | "mixed" | "conj"
        self.total = len(words)
        self.queue = weighted_order(words)
        self.done: set[tuple[str, str]] = set()
        self.missed: dict[tuple[str, str], Word] = {}
        self.attempts = 0
        self.hits = 0
        self.current: Word | None = None
        self.current_dir = ""
        self._new_miss = False
        self.next()

    def next(self) -> Word | None:
        self.current = self.queue.pop(0) if self.queue else None
        d = self.direction
        self.current_dir = random.choice(["ko→en", "en→ko"]) if d == "mixed" else d
        return self.current

    @property
    def prompt(self) -> str:
        return self.current.ask(self.current_dir)

    @property
    def answer(self) -> str:
        return self.current.expect(self.current_dir)

    def grade(self, correct: bool) -> None:
        w = self.current
        self.attempts += 1
        if correct:
            self.hits += 1
            self.done.add(w.key)
        else:
            self._new_miss = w.key not in self.missed
            self.missed[w.key] = w
            self.queue.insert(min(REQUEUE_GAP - 1, len(self.queue)), w)

    def override(self) -> None:
        """Last answer was a miss but the user says it was right."""
        w = self.current
        self.hits += 1
        self.done.add(w.key)
        if self._new_miss:
            self.missed.pop(w.key, None)
        for i, q in enumerate(self.queue):
            if q.key == w.key:
                del self.queue[i]
                break

    @property
    def pending(self) -> int:
        return len(set(self.missed) - self.done)

    @property
    def finished(self) -> bool:
        return self.current is None
