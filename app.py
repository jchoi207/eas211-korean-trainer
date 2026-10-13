"""Korean vocab trainer. Run: uv run app.py [--deck path/to/deck.md]"""

import argparse
import time
from collections import Counter
from pathlib import Path

from nicegui import ui

import conj_io
import vocab_io
from checking import check
from session import Session, select, worst

ROOT = Path(__file__).resolve().parent
DECKS = ROOT / "decks"
STATS = ROOT / "stats"
DECK = DECKS / "eas211" / "vocab.md"
STATS_FILE = vocab_io.stats_path(DECK, DECKS, STATS)
CONJ = DECK.parent / "conjugations.md"  # optional, enables Conjugate mode
CONJ_STATS = vocab_io.stats_path(CONJ, DECKS, STATS)

DIRECTIONS = {"ko→en": "한 → EN", "en→ko": "EN → 한", "mixed": "Mixed"}
DIRECTION_HINT = {"ko→en": "Korean → English", "en→ko": "English → Korean"}
MODES = {"learn": "Learn", "flash": "Flashcards", "type": "Typing", "conj": "Conjugate"}
POOLS = {"all": "All", "worst": "Worst"}
# Score cell tinted red (0) -> amber -> green (100); blank when untested.
SCORE_CELL = """
<q-td :props="props" :style="props.value == null ? '' : `background: hsla(${props.value * 1.2}, 75%, 50%, 0.35)`">
  {{ props.value }}
</q-td>
"""


def columns(names: list[str]) -> list[dict]:
    return [{"name": c, "label": c, "field": c, "sortable": True, "align": "left"} for c in names]


TABLE_COLUMNS = columns(vocab_io.COLUMNS)
CONJ_COLUMNS = columns(["korean", "form", "answer", "rule", "correct", "box", "score", "last"])

# Emit the input's DOM value on Enter. If the Enter only commits a Hangul
# syllable (IME still composing), wait for the composition to finish first.
ENTER_JS = """(e) => {
  const send = () => emit(e.target.value);
  if (e.isComposing) e.target.addEventListener('compositionend', () => setTimeout(send, 0), {once: true});
  else send();
}"""


def copy_stats(src, dst) -> None:
    if isinstance(src, conj_io.Card):
        dst.ok = src.ok
    else:
        dst.ko_en, dst.en_ko = src.ko_en, src.en_ko
    dst.box, dst.last = src.box, src.last


def check_target(item) -> str | None:
    """What typing accepts for a conjugation card: the answer, plus 죠 for 지요."""
    t = item.target if isinstance(item, conj_io.Card) else None
    if t and t.endswith("지요"):
        return f"{t}/{t[:-2]}죠"
    return t


class Trainer:
    def __init__(self):
        self.tags: set[str] = set()
        self.forms: set[str] = set()  # conjugate mode filters, empty = all
        self.rules: set[str] = set()
        self.direction = "ko→en"
        self.mode = "flash"
        self.pool = "all"
        self.worst_n = 20
        self.s: Session | None = None
        self.learn_words: list[vocab_io.Word] | None = None  # set while in learn mode
        self.learn_i = 0
        self.revealed = False  # card flipped, or typed answer checked
        self.prev_box = 0
        self.last_enter = 0.0
        self.root = ui.column().classes("w-full max-w-xl mx-auto gap-6 p-6")
        ui.keyboard(on_key=self.on_key)
        self.show_setup()

    # setup

    def show_setup(self):
        self.s = None
        self.learn_words = None
        self.words = vocab_io.load(DECK, STATS_FILE)
        self.cards, self.form_names = conj_io.load(CONJ, CONJ_STATS) if CONJ.exists() else ([], [])
        modes = MODES if self.cards else {k: v for k, v in MODES.items() if k != "conj"}
        self.root.clear()
        self.root.classes(remove="max-w-xl", add="max-w-4xl")  # room for the word table
        with self.root:
            ui.label("Korean vocab").classes("text-2xl font-semibold")
            ui.label("Mode").classes("text-sm opacity-60 -mb-4")
            ui.toggle(modes, value=self.mode, on_change=self.change_mode)
            self.tag_picker()
            self.conj_picker()
            with ui.column().classes("gap-6").bind_visibility_from(self, "mode", backward=lambda m: m in ("flash", "type")):
                ui.label("Direction").classes("text-sm opacity-60 -mb-4")
                ui.toggle(DIRECTIONS).bind_value(self, "direction")
            ui.label("Words").classes("text-sm opacity-60 -mb-4")
            with ui.row().classes("items-center gap-3"):
                ui.toggle(POOLS).bind_value(self, "pool")
                ui.number(min=1, step=5, precision=0).bind_value(self, "worst_n").bind_visibility_from(
                    self, "pool", value="worst"
                ).props("dense outlined").classes("w-24")
            ui.button("Start", on_click=lambda: self.start()).classes("w-full").props("unelevated size=lg")
            with ui.expansion("Word list").classes("w-full"):
                self.word_table()

    @property
    def conj(self) -> bool:
        return self.mode == "conj"

    def pool_items(self) -> list:
        """Words, or conjugation cards, matching the current pickers."""
        if not self.conj:
            return select(self.words, self.tags)
        return [
            c for c in select(self.cards, self.tags)
            if (not self.forms or c.form in self.forms) and (not self.rules or c.rule in self.rules)
        ]

    def change_mode(self, e):
        self.mode = e.value
        self.refresh_pickers()

    def refresh_pickers(self):
        self.tag_picker.refresh()
        self.conj_picker.refresh()
        self.word_table.refresh()

    @ui.refreshable_method
    def tag_picker(self):
        items = self.cards if self.conj else self.words
        counts = Counter(t for w in {w.korean: w for w in items}.values() for t in w.tags)  # words, not cards
        n = len(self.pool_items())
        ui.label(f"Sets · {n} {'cards' if self.conj else 'words'}").classes("text-sm opacity-60 -mb-4")
        with ui.row().classes("gap-1"):
            self.chip("all", not self.tags, lambda: self.clear(self.tags))
            for t in sorted(counts):
                self.chip(f"{t} · {counts[t]}", t in self.tags, lambda t=t: self.toggle(self.tags, t))

    @ui.refreshable_method
    def conj_picker(self):
        if not self.conj:
            return
        rules = sorted({c.rule for c in self.cards})
        for label, chosen, names in (("Forms", self.forms, self.form_names), ("Rules", self.rules, rules)):
            ui.label(label).classes("text-sm opacity-60 -mb-4")
            with ui.row().classes("gap-1"):
                self.chip("all", not chosen, lambda chosen=chosen: self.clear(chosen))
                for x in names:
                    self.chip(x, x in chosen, lambda chosen=chosen, x=x: self.toggle(chosen, x))

    @ui.refreshable_method
    def word_table(self):
        if self.conj:
            self.conj_tables()
            return
        rows = [
            {
                "id": i,
                "korean": w.korean,
                "english": w.english,
                "tags": " ".join(w.tags),
                "notes": w.notes,
                "ko→en": vocab_io.fmt_ratio(w.ko_en),
                "en→ko": vocab_io.fmt_ratio(w.en_ko),
                "box": w.box,
                "score": w.score,
                "last": w.last,
            }
            # weakest first, untested last
            for i, w in enumerate(sorted(select(self.words, self.tags), key=lambda w: (w.score is None, w.score or 0)))
        ]
        table = ui.table(columns=TABLE_COLUMNS, rows=rows, pagination=0).props("flat dense").classes("w-full")
        table.add_slot("body-cell-score", SCORE_CELL)
        with table.add_slot("top-right"):
            ui.input(placeholder="Search").bind_value(table, "filter").props("dense clearable")

    def conj_tables(self):
        cards = sorted(self.pool_items(), key=lambda c: (c.score is None, c.score or 0))
        rows = [
            {"id": i, "korean": c.korean, "form": c.form, "answer": c.target, "rule": c.rule,
             "correct": vocab_io.fmt_ratio(c.ok), "box": c.box, "score": c.score, "last": c.last}
            for i, c in enumerate(cards)
        ]
        with ui.row().classes("w-full gap-4 no-wrap items-start"):
            for attr in ("rule", "form"):  # accuracy per rule and per form
                summ = [dict(r, id=i) for i, r in enumerate(conj_io.summary(cards, attr))]
                t = ui.table(columns=columns([attr, "cards", "correct", "pct"]), rows=summ, pagination=0)
                t.props("flat dense").classes("flex-1")
                t.add_slot("body-cell-pct", SCORE_CELL)
        table = ui.table(columns=CONJ_COLUMNS, rows=rows, pagination=0).props("flat dense").classes("w-full")
        table.add_slot("body-cell-score", SCORE_CELL)
        with table.add_slot("top-right"):
            ui.input(placeholder="Search").bind_value(table, "filter").props("dense clearable")

    @staticmethod
    def chip(text: str, selected: bool, on_click):
        c = ui.chip(text, selectable=True, selected=selected, on_click=on_click)
        if not selected:
            c.props("outline")

    def toggle(self, chosen: set[str], x: str):
        chosen ^= {x}
        self.refresh_pickers()

    def clear(self, chosen: set[str]):
        chosen.clear()
        self.refresh_pickers()

    def start(self, words: list | None = None):
        if words is None:
            self.words = vocab_io.load(DECK, STATS_FILE)
            if self.cards:
                self.cards, self.form_names = conj_io.load(CONJ, CONJ_STATS)
            words = self.pool_items()
            if self.pool == "worst":
                words = worst(words, int(self.worst_n or 1), "conj" if self.conj else self.direction)
        if not words:
            ui.notify("Nothing in the selected sets", type="warning")
            return
        if self.mode == "learn":
            self.learn_words, self.learn_i = words, 0
            self.show_learn()
            return
        self.s = Session(words, "conj" if self.conj else self.direction)
        self.show_card()

    # learn mode: browse pairs in file order, nothing graded or saved

    def show_learn(self):
        words, i = self.learn_words, self.learn_i
        w = words[i]
        self.root.clear()
        self.root.classes(remove="max-w-4xl", add="max-w-xl")
        with self.root:
            with ui.row().classes("w-full items-center justify-between no-wrap"):
                ui.button(icon="arrow_back", on_click=self.show_setup).props("flat round")
                ui.label(f"{i + 1} / {len(words)}").classes("opacity-70")
                ui.space()
            with ui.card().classes("w-full min-h-64 items-center justify-center gap-3 p-8"):
                with ui.row().classes("w-full items-center justify-around gap-8"):
                    ui.label(w.korean).classes("text-4xl text-center leading-tight")
                    ui.label(w.english).classes("text-2xl text-center opacity-80")
                if w.notes:
                    ui.label(w.notes).classes("text-sm opacity-60 text-center")
            with ui.row().classes("w-full gap-3 no-wrap"):
                ui.button("←  Prev", on_click=lambda: self.learn_step(-1)).classes("flex-1").props(
                    "outline" + (" disable" if i == 0 else "")
                )
                last = i == len(words) - 1
                ui.button("Done" if last else "Next  →", on_click=lambda: self.learn_step(1)).classes("flex-1").props("unelevated")
            ui.label("← → or Space to move").classes("text-xs opacity-50 self-center")

    def learn_step(self, d: int):
        i = self.learn_i + d
        if i >= len(self.learn_words):
            self.show_setup()
        elif i >= 0:
            self.learn_i = i
            self.show_learn()

    # card

    def show_card(self):
        s = self.s
        if s.finished:
            self.show_end()
            return
        self.revealed = False
        self.root.clear()
        self.root.classes(remove="max-w-4xl", add="max-w-xl")
        with self.root:
            with ui.row().classes("w-full items-center justify-between no-wrap"):
                ui.button(icon="arrow_back", on_click=self.show_setup).props("flat round")
                retry = f" · {s.pending} to retry" if s.pending else ""
                ui.label(f"{len(s.done)} / {s.total}{retry}").classes("opacity-70")
                if self.conj:
                    ui.space()
                else:
                    ui.toggle(DIRECTIONS, value=s.direction, on_change=self.change_direction).props("dense")
            with ui.card().classes("w-full min-h-64 items-center justify-center gap-3 p-8") as card:
                if self.conj:
                    ui.label(s.current.english).classes("text-sm opacity-50")
                    ui.label(s.prompt).classes("text-5xl text-center leading-tight")
                    ui.chip(s.current.form).props("color=primary text-color=white")
                else:
                    ui.label(DIRECTION_HINT[s.current_dir]).classes("text-xs uppercase tracking-wide opacity-50")
                    ui.label(s.prompt).classes("text-5xl text-center leading-tight")
                self.back = ui.column().classes("items-center gap-1")
            if self.mode == "flash":
                card.classes("cursor-pointer").on("click", self.flip)
                self.grade_row = ui.row().classes("w-full gap-3 no-wrap")
                with self.grade_row:
                    ui.button("Missed  ←", on_click=lambda: self.grade_flash(False), color="negative").classes("flex-1").props("unelevated")
                    ui.button("Got it  →", on_click=lambda: self.grade_flash(True), color="positive").classes("flex-1").props("unelevated")
                self.grade_row.set_visibility(False)
                ui.label("Space or click to flip").classes("text-xs opacity-50 self-center")
            else:
                target = "conjugated form" if self.conj else "English" if s.current_dir == "ko→en" else "Korean"
                self.input = ui.input(placeholder=f"Type the {target}").props("outlined autofocus").classes("w-full text-xl")
                self.input.on("keydown.enter", lambda e: self.on_enter(e.args), js_handler=ENTER_JS)
                self.feedback = ui.column().classes("w-full items-center gap-2")

    def change_direction(self, e):
        self.s.direction = e.value
        if not self.revealed:
            self.s.current_dir = e.value if e.value != "mixed" else self.s.current_dir
            self.show_card()

    def reveal_answer(self):
        w = self.s.current
        with self.back:
            ui.separator().classes("w-24 my-2")
            ui.label(self.s.answer).classes("text-3xl text-center")
            hint = w.rule if self.conj else w.notes
            if hint:
                ui.label(hint).classes("text-sm opacity-60 text-center")

    def save(self, correct: bool):
        s, w = self.s, self.s.current
        self.prev_box = w.box
        if self.conj:
            copy_stats(conj_io.record(CONJ_STATS, w.key, correct), w)
        else:
            copy_stats(vocab_io.record(STATS_FILE, w.key, s.current_dir, correct), w)
        s.grade(correct)

    def advance(self):
        self.s.next()
        self.show_card()

    # flashcard mode

    def flip(self):
        if self.revealed:
            return
        self.revealed = True
        self.reveal_answer()
        self.grade_row.set_visibility(True)

    def grade_flash(self, correct: bool):
        if not self.revealed:
            return
        self.save(correct)
        self.advance()

    # typing mode

    def on_enter(self, value):
        now = time.monotonic()
        if now - self.last_enter < 0.3:  # IME can fire a second Enter
            return
        self.last_enter = now
        if self.revealed:
            self.advance()
            return
        self.revealed = True
        correct = check(value or "", check_target(self.s.current) or self.s.answer)
        self.save(correct)
        self.input.props("readonly")
        self.reveal_answer()
        self.show_feedback(correct)

    def show_feedback(self, correct: bool):
        self.feedback.clear()
        with self.feedback:
            if correct:
                ui.label("✓ Correct").classes("text-lg text-positive")
            else:
                ui.label("✗ Not quite").classes("text-lg text-negative")
                ui.button("I was right", on_click=self.override).props("flat dense no-caps")
            ui.label("Enter to continue").classes("text-xs opacity-50")

    def override(self):
        s, w = self.s, self.s.current
        if self.conj:
            copy_stats(conj_io.undo_miss(CONJ_STATS, w.key, self.prev_box), w)
        else:
            copy_stats(vocab_io.undo_miss(STATS_FILE, w.key, s.current_dir, self.prev_box), w)
        s.override()
        self.show_feedback(True)
        self.input.run_method("focus")

    # keyboard (ignored while focus is in the text input)

    def on_key(self, e):
        if not e.action.keydown or e.action.repeat:
            return
        if self.learn_words is not None:
            if e.key.arrow_left:
                self.learn_step(-1)
            elif e.key.arrow_right or e.key.space:
                self.learn_step(1)
            return
        if self.s is None or self.s.finished:
            return
        if self.mode == "flash":
            if e.key.space:
                self.flip()
            elif e.key.arrow_left:
                self.grade_flash(False)
            elif e.key.arrow_right:
                self.grade_flash(True)
        elif e.key.enter and self.revealed:
            self.on_enter(None)

    # end

    def show_end(self):
        s = self.s
        self.root.clear()
        with self.root:
            ui.label("Done").classes("text-2xl font-semibold")
            pct = round(100 * s.hits / s.attempts) if s.attempts else 0
            ui.label(f"{s.hits} / {s.attempts} correct ({pct}%)").classes("opacity-70")
            if s.missed:
                ui.label("Missed").classes("text-sm opacity-60 -mb-4")
                with ui.card().classes("w-full gap-1"):
                    for w in s.missed.values():
                        with ui.row().classes("w-full justify-between"):
                            ui.label(f"{w.korean} · {w.form}" if self.conj else w.korean).classes("text-lg")
                            ui.label(w.target if self.conj else w.english).classes("opacity-70")
            with ui.row().classes("w-full gap-3 no-wrap"):
                ui.button("Again", on_click=lambda: self.start()).classes("flex-1").props("unelevated")
                if s.missed:
                    missed = list(s.missed.values())
                    ui.button("Missed only", on_click=lambda: self.start(missed)).classes("flex-1").props("outline")
                ui.button("Setup", on_click=self.show_setup).classes("flex-1").props("flat")


@ui.page("/")
def index():
    ui.query("body").style("font-family: -apple-system, 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif")
    Trainer()


if __name__ in {"__main__", "__mp_main__"}:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", type=Path, default=DECK)
    parser.add_argument("--port", type=int, default=8520)
    args = parser.parse_args()
    DECK = args.deck.resolve()
    STATS_FILE = vocab_io.stats_path(DECK, DECKS, STATS)
    CONJ = DECK.parent / "conjugations.md"
    CONJ_STATS = vocab_io.stats_path(CONJ, DECKS, STATS)
    ui.run(title="Korean vocab", dark=None, reload=False, port=args.port)
