"""Numbers study: random questions from numdrill, nothing saved."""

import random
import time
from typing import Callable

from nicegui import ui

from trainer.numdrill.questions import CATEGORIES, RANGED, Q, make, usable
from trainer.numdrill.sino import MAX as SINO_MAX
from trainer.ui.widgets import ENTER_JS, MODES

DIRECTIONS = {"num→ko": "123/EN → 한", "ko→num": "한 → 123/EN", "mixed": "Mixed"}


class NumbersScreen:
    def __init__(self, root: ui.column, on_exit: Callable[[], None]):
        self.root, self.on_exit = root, on_exit
        self.lo, self.hi = 0, 100
        self.cats: set[str] = set()  # empty = all
        self.tens = False  # native: only 10, 20, ... 90
        self.dir = "num→ko"
        self.mode = "flash"
        self.item: Q | None = None  # question on screen
        self.cur = "num→ko"
        self.hits = self.tries = 0
        self.revealed = False
        self.last_enter = 0.0

    def setup(self):
        ui.label("Category").classes("text-sm opacity-60 -mb-4")
        self.category_picker()
        ui.label("Mode").classes("text-sm opacity-60 -mb-4")
        ui.toggle(MODES).bind_value(self, "mode")
        ui.label("Direction").classes("text-sm opacity-60 -mb-4").bind_visibility_from(
            self, "mode", backward=lambda m: m != "learn"
        )
        ui.toggle(DIRECTIONS).bind_value(self, "dir").bind_visibility_from(
            self, "mode", backward=lambda m: m != "learn"
        )
        in_range = lambda cats: not cats or bool(cats & RANGED)
        ui.label("Range (native and counting: 1 to 99)").classes("text-sm opacity-60 -mb-4").bind_visibility_from(
            self, "cats", backward=in_range
        )
        with ui.row().classes("items-center gap-3").bind_visibility_from(self, "cats", backward=in_range):
            for label, attr in (("From", "lo"), ("To", "hi")):
                ui.number(label=label, min=0, max=SINO_MAX, step=10, precision=0).bind_value(self, attr).props(
                    "dense outlined"
                ).classes("w-36")
        ui.checkbox("Native: tens only (10 to 90, ignores range)").bind_value(self, "tens").bind_visibility_from(
            self, "cats", backward=lambda cats: not cats or "native" in cats
        )
        ui.button("Start", on_click=self.start).classes("w-full").props("unelevated size=lg")

    def category_picker(self):
        """Dropdown multi-select. Empty = all categories."""
        def shown(chosen: set[str]) -> str:
            return ", ".join(CATEGORIES[c] for c in CATEGORIES if c in chosen) or "all"

        def on_change(e):
            self.cats = set(e.value or [])  # reassign, so the range inputs' visibility binding sees it
            sel.props(f'display-value="{shown(self.cats)}"')

        sel = ui.select(CATEGORIES, multiple=True, value=[c for c in CATEGORIES if c in self.cats], on_change=on_change)
        sel.props(f'dense outlined clearable options-dense display-value="{shown(self.cats)}"').classes("w-full")

    def on_key(self, e):
        if self.mode == "type":
            if e.key.enter and self.revealed:
                self.on_enter(None)
        elif self.mode == "learn":
            if e.key.enter or e.key.space or e.key.arrow_right:
                self.next()
        elif e.key.space:
            self.flip()
        elif e.key.arrow_left:
            self.grade(False)
        elif e.key.arrow_right:
            self.grade(True)

    def start(self):
        lo, hi = int(self.lo or 0), int(self.hi or 0)
        if lo > hi:
            ui.notify("From is above To", type="warning")
            return
        if not usable(self.cats, lo, hi, self.tens):
            ui.notify("Range is outside these categories (native numbers go 1 to 99)", type="warning")
            return
        self.hits = self.tries = 0
        self.next()

    def next(self):
        self.item = make(self.cats, int(self.lo or 0), int(self.hi or 0), self.tens)
        d = self.dir
        self.cur = random.choice(["num→ko", "ko→num"]) if d == "mixed" else d
        self.show()

    def show(self):
        q, to_ko = self.item, self.cur == "num→ko"
        self.revealed = False
        self.root.clear()
        self.root.classes(remove="max-w-4xl", add="max-w-xl")
        with self.root:
            with ui.row().classes("w-full items-center justify-between no-wrap"):
                ui.button(icon="arrow_back", on_click=self.on_exit).props("flat round")
                if self.mode != "learn":
                    ui.label(f"{self.hits} / {self.tries}").classes("opacity-70")
            with ui.card().classes("w-full min-h-64 items-center justify-center gap-3 p-8") as card:
                ui.label(q.prompt if to_ko or self.mode == "learn" else q.ko).classes("text-5xl text-center leading-tight")
                self.back = ui.column().classes("items-center gap-1")
            if self.mode == "learn":
                self.revealed = True
                with self.back:
                    ui.separator().classes("w-24 my-2")
                    ui.label(q.ko).classes("text-3xl text-center")
                ui.button("Next  →", on_click=self.next).classes("w-full").props("unelevated")
                ui.label("Space or → for next").classes("text-xs opacity-50 self-center")
                return
            if self.mode == "flash":
                card.classes("cursor-pointer").on("click", self.flip)
                self.grade_row = ui.row().classes("w-full gap-3 no-wrap")
                with self.grade_row:
                    ui.button("Missed  ←", on_click=lambda: self.grade(False), color="negative").classes("flex-1").props("unelevated")
                    ui.button("Got it  →", on_click=lambda: self.grade(True), color="positive").classes("flex-1").props("unelevated")
                self.grade_row.set_visibility(False)
                ui.label("Space or click to flip").classes("text-xs opacity-50 self-center")
                return
            self.input = ui.input(placeholder="Type the Korean" if to_ko else "Type the number or English")
            self.input.props("outlined autofocus").classes("w-full text-xl")
            self.input.on("keydown.enter", lambda e: self.on_enter(e.args), js_handler=ENTER_JS)
            self.feedback = ui.column().classes("w-full items-center gap-2")

    def flip(self):
        if self.revealed:
            return
        self.revealed = True
        q = self.item
        with self.back:
            ui.separator().classes("w-24 my-2")
            ui.label(q.ko if self.cur == "num→ko" else q.prompt).classes("text-3xl text-center")
        self.grade_row.set_visibility(True)

    def grade(self, correct: bool):
        if not self.revealed:
            return
        self.tries += 1
        self.hits += correct
        self.next()

    def on_enter(self, value):
        now = time.monotonic()
        if now - self.last_enter < 0.3:  # IME can fire a second Enter
            return
        self.last_enter = now
        if self.revealed:
            self.next()
            return
        self.revealed = True
        q, to_ko = self.item, self.cur == "num→ko"
        answer = (value or "").strip()
        correct = q.ko_ok(answer) if to_ko else q.en_ok(answer)
        self.tries += 1
        self.hits += correct
        self.input.props("readonly")
        with self.back:
            ui.separator().classes("w-24 my-2")
            ui.label(q.ko if to_ko else q.prompt).classes("text-3xl text-center")
        with self.feedback:
            ui.label("✓ Correct" if correct else "✗ Not quite").classes(f"text-lg text-{'positive' if correct else 'negative'}")
            ui.label("Enter to continue").classes("text-xs opacity-50")
