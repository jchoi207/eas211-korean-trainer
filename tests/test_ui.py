"""Smoke test: every screen renders without error."""

import pytest
from nicegui import ui
from nicegui.testing import User

from trainer.paths import DEFAULT_DECK, Paths
from trainer.ui.trainer import Trainer


def page(tmp_path):
    paths = Paths.for_deck(DEFAULT_DECK)
    paths = Paths(paths.deck, tmp_path / "v.json", paths.conj, tmp_path / "c.json", tmp_path / "starred.json")

    @ui.page("/")
    def index():
        index.trainer = Trainer(paths)

    return index


@pytest.mark.parametrize("study, mode", [("words", "learn"), ("words", "flash"), ("words", "type"), ("conj", "learn"), ("conj", "flash"), ("conj", "type")])
async def test_study_screens(user: User, tmp_path, study, mode):
    index = page(tmp_path)
    await user.open("/")
    t = index.trainer
    t.study, t.mode = study, mode
    t.show_setup()
    t.start()
    assert t.learn_words is not None if mode == "learn" else t.s is not None


@pytest.mark.parametrize("mode", ["learn", "flash", "type"])
async def test_numbers_screens(user: User, tmp_path, mode):
    index = page(tmp_path)
    await user.open("/")
    t = index.trainer
    t.study = "numbers"
    t.show_setup()
    t.numbers.mode = mode
    t.numbers.start()
    assert t.numbers.item is not None
    t.numbers.next()
