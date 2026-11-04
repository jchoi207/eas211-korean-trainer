"""Setup screen for words and conjugations: pickers, word list, stars in the table.

Mixed into Trainer; expects its state (study, mode, tags, forms, rules, pool, words, cards, starred, ...).
"""

from collections import Counter

from nicegui import ui

from trainer.data import conjugations, stats, vocab
from trainer.study.session import select
from trainer.ui.widgets import (
    CONJ_COLUMNS, DIRECTIONS, MODES, POOLS, SCORE_CELL, STAR_CELL, STUDY, TABLE_COLUMNS, columns,
)


class SetupMixin:
    # setup

    def show_setup(self):
        self.s = None
        self.learn_words = None
        self.numbers.item = None
        self.words = vocab.load(self.paths.deck, self.paths.stats)
        self.cards, self.form_names = conjugations.load(self.paths.conj, self.paths.conj_stats) if self.paths.conj.exists() else ([], [])
        self.starred = stats.load_starred(self.paths.starred)
        if not self.cards and self.study == "conj":
            self.study = "words"
        if self.tags_study != self.study:  # tags don't carry between words and conjugations
            self.tags_study = self.study
            self.tags.clear()
            self.default_latest = True
        if self.study == "words" and self.default_latest:
            self.default_latest = False
            if all_tags := {t for w in self.words for t in w.tags}:
                self.tags.clear()
                self.tags.add(max(all_tags))  # lNN-cN sorts chronologically
        self.root.clear()
        self.root.classes(remove="max-w-xl", add="max-w-4xl")  # room for the word table
        with self.root:
            ui.label("Korean vocab").classes("text-2xl font-semibold")
            if found := conjugations.problems(self.words, self.cards):
                ui.label("Deck collisions (python conjugations.py): " + "; ".join(found)).classes("text-sm text-negative")
            ui.label("Study").classes("text-sm opacity-60 -mb-4")
            study = {k: v for k, v in STUDY.items() if k != "conj" or self.cards}
            ui.toggle(study, value=self.study, on_change=self.change_study)
            if self.study == "numbers":
                self.numbers.setup()
                return
            ui.label("Mode").classes("text-sm opacity-60 -mb-4")
            ui.toggle(MODES, value=self.mode, on_change=lambda e: self.change("mode", e.value))
            self.tag_picker()
            self.options_picker()
            ui.label("Words").classes("text-sm opacity-60 -mb-4")
            with ui.row().classes("items-center gap-3"):
                ui.toggle(POOLS, value=self.pool, on_change=lambda e: self.change("pool", e.value))
                ui.number(min=1, step=5, precision=0).bind_value(self, "worst_n").bind_visibility_from(
                    self, "pool", value="worst"
                ).props("dense outlined").classes("w-24")
            ui.button("Start", on_click=lambda: self.start()).classes("w-full").props("unelevated size=lg")
            with ui.expansion("Word list").classes("w-full"):
                self.word_table()

    def change_study(self, e):
        self.study = e.value
        self.show_setup()
    @property
    def conj(self) -> bool:
        return self.study == "conj"

    def pool_items(self) -> list:
        """Words, or conjugation cards, matching the current pickers."""
        items = select(self.cards if self.conj else self.words, self.tags)
        if self.conj:
            items = [c for c in items if (not self.forms or c.form in self.forms) and (not self.rules or c.rule in self.rules)]
        if self.pool == "starred":
            items = [w for w in items if w.korean in self.starred]
        return items

    def change(self, attr: str, value: str):
        setattr(self, attr, value)
        self.refresh_pickers()

    def refresh_pickers(self):
        self.tag_picker.refresh()
        self.options_picker.refresh()
        self.word_table.refresh()

    @ui.refreshable_method
    def tag_picker(self):
        items = self.cards if self.conj else self.words
        counts = Counter(t for w in {w.korean: w for w in items}.values() for t in w.tags)  # words, not cards
        self.count_label = ui.label().classes("text-sm opacity-60 -mb-4")
        self.update_count()
        self.multi(self.tags, {t: f"{t} · {counts[t]}" for t in sorted(counts)})

    def update_count(self):
        n = len(self.pool_items())
        self.count_label.text = f"Sets · {n} {'cards' if self.conj else 'words'}"

    @ui.refreshable_method
    def options_picker(self):
        """Forms and rules for conjugations, direction for words (except in learn mode)."""
        if not self.conj:
            if self.mode != "learn":
                ui.label("Direction").classes("text-sm opacity-60 -mb-4")
                ui.toggle(DIRECTIONS).bind_value(self, "direction")
            return
        rules = sorted({c.rule for c in self.cards})
        for label, chosen, names in (("Forms", self.forms, self.form_names), ("Rules", self.rules, rules)):
            ui.label(label).classes("text-sm opacity-60 -mb-4")
            self.multi(chosen, {x: x for x in names})

    @ui.refreshable_method
    def word_table(self):
        if self.conj:
            self.conj_tables()
            return
        rows = [
            {
                "id": i,
                "star": w.korean in self.starred,
                "korean": w.korean,
                "english": w.english,
                "tags": " ".join(w.tags),
                "notes": w.notes,
                "ko→en": stats.fmt_ratio(w.ko_en),
                "en→ko": stats.fmt_ratio(w.en_ko),
                "box": w.box,
                "score": w.score,
                "last": w.last,
            }
            # weakest first, untested last
            for i, w in enumerate(sorted(self.pool_items(), key=lambda w: (w.score is None, w.score or 0)))
        ]
        table = ui.table(columns=TABLE_COLUMNS, rows=rows, pagination=0).props("flat dense").classes("w-full")
        table.add_slot("body-cell-score", SCORE_CELL)
        self.star_cells(table)
        with table.add_slot("top-right"):
            ui.input(placeholder="Search").bind_value(table, "filter").props("dense clearable")

    def conj_tables(self):
        cards = sorted(self.pool_items(), key=lambda c: (c.score is None, c.score or 0))
        rows = [
            {"id": i, "star": c.korean in self.starred, "korean": c.korean, "form": c.form, "answer": c.target, "rule": c.rule,
             "correct": stats.fmt_ratio(c.ok), "box": c.box, "score": c.score, "last": c.last}
            for i, c in enumerate(cards)
        ]
        with ui.row().classes("w-full gap-4 no-wrap items-start"):
            for attr in ("rule", "form"):  # accuracy per rule and per form
                summ = [dict(r, id=i) for i, r in enumerate(conjugations.summary(cards, attr))]
                t = ui.table(columns=columns([attr, "cards", "correct", "pct"]), rows=summ, pagination=0)
                t.props("flat dense").classes("flex-1")
                t.add_slot("body-cell-pct", SCORE_CELL)
        table = ui.table(columns=CONJ_COLUMNS, rows=rows, pagination=0).props("flat dense").classes("w-full")
        table.add_slot("body-cell-score", SCORE_CELL)
        self.star_cells(table)
        with table.add_slot("top-right"):
            ui.input(placeholder="Search").bind_value(table, "filter").props("dense clearable")

    def multi(self, chosen: set[str], options: dict[str, str]):
        """Dropdown multi-select over options {value: label}, editing chosen in place. Empty = all."""
        def shown() -> str:
            return ", ".join(x for x in options if x in chosen) or "all"

        def on_change(e):
            chosen.clear()
            chosen.update(e.value or [])
            sel.props(f'display-value="{shown()}"')
            self.update_count()  # don't refresh the pickers, that would close the dropdown
            self.word_table.refresh()

        sel = ui.select(options, multiple=True, value=[x for x in options if x in chosen], on_change=on_change)
        sel.props(f'dense outlined clearable options-dense display-value="{shown()}"').classes("w-full")

    # stars

    def star_cells(self, table):
        table.add_slot("body-cell-star", STAR_CELL)

        def on_star(e):
            self.starred = stats.toggle_star(self.paths.starred, e.args)
            self.update_count()
            self.word_table.refresh()

        table.on("star", on_star)
