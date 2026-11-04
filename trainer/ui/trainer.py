"""Korean vocab trainer UI: the Trainer shell, keyboard routing, and the NiceGUI page."""

from pathlib import Path

from nicegui import ui

from trainer.paths import Paths
from trainer.study.session import Session
from trainer.ui.numbers import NumbersScreen
from trainer.ui.setup import SetupMixin
from trainer.ui.study import StudyMixin

FAVICON = Path(__file__).with_name("favicon.svg")


class Trainer(SetupMixin, StudyMixin):
    def __init__(self, paths: Paths):
        self.paths = paths
        self.tags: set[str] = set()
        self.tags_study = ""  # study the current tags were picked for
        self.default_latest = True  # next words setup preselects the latest lesson
        self.forms: set[str] = set()  # conjugation filters, empty = all
        self.rules: set[str] = set()
        self.study = "words"
        self.direction = "ko→en"
        self.mode = "flash"
        self.pool = "all"
        self.worst_n = 20
        self.starred: set[str] = set()  # Korean words, shared by words and conjugations
        self.s: Session | None = None
        self.learn_words: list | None = None  # Words, or lists of one verb's Cards; set while in learn mode
        self.learn_i = 0
        self.revealed = False  # card flipped, or typed answer checked
        self.prev_box = 0
        self.last_enter = 0.0
        self.root = ui.column().classes("w-full max-w-xl mx-auto gap-6 p-6")
        self.numbers = NumbersScreen(self.root, self.show_setup)
        ui.keyboard(on_key=self.on_key)
        self.show_setup()

    # keyboard (ignored while focus is in the text input)

    def on_key(self, e):
        if not e.action.keydown or e.action.repeat:
            return
        if self.numbers.item is not None:
            self.numbers.on_key(e)
            return
        on_card = self.learn_words is not None or (self.s is not None and not self.s.finished)
        if on_card and e.key.code == "KeyS":  # physical key, so it works with a Korean layout too
            self.toggle_star()
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


def run(deck: Path, port: int) -> None:
    paths = Paths.for_deck(deck)

    @ui.page("/")
    def index():
        ui.query("body").style("font-family: -apple-system, 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif")
        Trainer(paths)

    ui.run(title="Korean vocab", favicon=FAVICON, dark=None, reload=False, port=port)
