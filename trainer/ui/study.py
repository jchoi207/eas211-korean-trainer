"""Study screens for words and conjugations: learn, flashcards, typing, and the end screen.

Mixed into Trainer; expects its state (s, mode, learn_words, revealed, ...).
"""

import time

from nicegui import ui

from trainer.data import conjugations, stats, vocab
from trainer.study.checking import check
from trainer.study.session import Session, worst
from trainer.ui.widgets import DIRECTION_HINT, DIRECTIONS, ENTER_JS


def copy_stats(src, dst) -> None:
    if isinstance(src, conjugations.Card):
        dst.ok = src.ok
    else:
        dst.ko_en, dst.en_ko = src.ko_en, src.en_ko
    dst.box, dst.last = src.box, src.last


def check_target(item) -> str | None:
    """What typing accepts for a conjugation card: the answer, plus 죠 for 지요."""
    t = item.target if isinstance(item, conjugations.Card) else None
    if t and t.endswith("지요"):
        return f"{t}/{t[:-2]}죠"
    return t


class StudyMixin:
    # stars

    def star_button(self, korean: str):
        """Star toggle for the word on screen. S on the keyboard does the same."""
        self.star_korean = korean
        self.star_btn = ui.button(on_click=self.toggle_star).props("flat round").mark("star")
        self.paint_star()

    def paint_star(self):
        on = self.star_korean in self.starred
        self.star_btn.props(f"icon={'star' if on else 'star_border'} color={'amber' if on else 'grey'}")

    def toggle_star(self):
        self.starred = stats.toggle_star(self.paths.starred, self.star_korean)
        self.paint_star()
    def start(self, words: list | None = None):
        if words is None:
            self.words = vocab.load(self.paths.deck, self.paths.stats)
            if self.cards:
                self.cards, self.form_names = conjugations.load(self.paths.conj, self.paths.conj_stats)
            words = self.pool_items()
            if self.pool == "worst":
                words = worst(words, int(self.worst_n or 1), "conj" if self.conj else self.direction)
        if not words:
            ui.notify("Nothing in the selected sets", type="warning")
            return
        if self.mode == "learn":
            self.learn_words, self.learn_i = (self.learn_groups(words) if self.conj else words), 0
            self.show_learn()
            return
        self.s = Session(words, "conj" if self.conj else self.direction)
        self.show_card()

    def learn_groups(self, cards: list[conjugations.Card]) -> list[list[conjugations.Card]]:
        """One group per verb, ordered by rule (table order of first appearance), then table order."""
        rank = {}
        for c in self.cards:
            rank.setdefault(c.rule, len(rank))
        order = {c.korean: i for i, c in reversed(list(enumerate(self.cards)))}
        groups: dict[str, list[conjugations.Card]] = {}
        for c in sorted(cards, key=lambda c: (order[c.korean], self.form_names.index(c.form))):
            groups.setdefault(c.korean, []).append(c)
        return sorted(groups.values(), key=lambda g: (rank[g[0].rule], order[g[0].korean]))

    # learn mode: browse in file order (conjugations: one verb with its forms), nothing graded or saved

    def show_learn(self):
        words, i = self.learn_words, self.learn_i
        w = words[i]
        self.root.clear()
        self.root.classes(remove="max-w-4xl", add="max-w-xl")
        with self.root:
            with ui.row().classes("w-full items-center justify-between no-wrap"):
                ui.button(icon="arrow_back", on_click=self.show_setup).props("flat round")
                ui.label(f"{i + 1} / {len(words)}").classes("opacity-70")
                self.star_button(w[0].korean if self.conj else w.korean)
            with ui.card().classes("w-full min-h-64 items-center justify-center gap-3 p-8"):
                if self.conj:
                    self.learn_conj(w)
                else:
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
            ui.label("← → or Space to move, S to star").classes("text-xs opacity-50 self-center")

    @staticmethod
    def learn_conj(group: list[conjugations.Card]):
        c = group[0]
        ui.label(c.korean).classes("text-4xl text-center leading-tight")
        ui.label(f"{c.english} · {c.rule}").classes("text-sm opacity-60 text-center")
        with ui.grid(columns=2).classes("gap-x-8 gap-y-2 mt-4 items-baseline"):
            for c in group:
                ui.label(c.form).classes("text-sm opacity-60 text-right")
                ui.label(c.target).classes("text-2xl")

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
                with ui.row().classes("items-center gap-1 no-wrap"):
                    if not self.conj:
                        ui.toggle(DIRECTIONS, value=s.direction, on_change=self.change_direction).props("dense")
                    self.star_button(s.current.korean)
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
                ui.label("Space or click to flip, S to star").classes("text-xs opacity-50 self-center")
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
            copy_stats(conjugations.record(self.paths.conj_stats, w.key, correct), w)
        else:
            copy_stats(vocab.record(self.paths.stats, w.key, s.current_dir, correct), w)
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
            copy_stats(conjugations.undo_miss(self.paths.conj_stats, w.key, self.prev_box), w)
        else:
            copy_stats(vocab.undo_miss(self.paths.stats, w.key, s.current_dir, self.prev_box), w)
        s.override()
        self.show_feedback(True)
        self.input.run_method("focus")

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
