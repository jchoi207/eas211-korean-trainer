# eas211-korean-trainer

NiceGUI app for drilling Korean vocab from markdown decks. Public repo, lives inside an Obsidian vault.

## Layout

Run with `uv run python -m trainer` (`--deck`, `--port`). Tests: `uv run pytest`.

- `trainer/__main__.py`: args, starts the app. `paths.py`: deck, stats and starred paths.
- `trainer/ui/`: NiceGUI. `trainer.py` is the `Trainer` shell (state, keyboard routing, page). `setup.py` (Study then Mode pickers, word list), `study.py` (learn, flashcards, typing, end screen), `numbers.py` (`NumbersScreen`, own state), `widgets.py` (shared constants). Setup and study are mixins on `Trainer`.
- `trainer/study/`: `session.py` (word selection, weighted order, requeueing misses), `checking.py` (lenient typed-answer matching).
- `trainer/data/`: `stats.py` (stats JSON, stars, paths), `table.py` (markdown table parsing), `vocab.py` (`Word`, decks), `conjugations.py` (`Card`, one per word x form, per-rule/form summaries, deck collision check; derived forms like 고 싶어해요 live in `DERIVED`).
- `trainer/numdrill/`: Numbers study questions by category (`questions.py`), Sino-Korean reading (`sino.py`).
- `session.py` works on both `Word` and `conjugations.Card` via `key`, `stats()`, `ask()`, `expect()`.
- `decks/<course>/<name>.md`: tracked. Columns `korean | english | tags | notes` only.
- `decks/<course>/conjugations.md`: `korean | english | tags | pos | rule | <form>...`, `nan` where a form doesn't exist. Edit via the `conjugate` skill.
- `stats/<course>/<name>.json`: gitignored, per-user progress.
- `tests/`: unit tests, deck collision check, and a render smoke test for every screen.

## Rules

- The app never writes decks. All progress goes to `stats/`.
- Stats are keyed by `korean\tenglish`. Changing either field orphans that word's stats.
- One row per Korean word in each deck. A word with two meanings or lessons is one row: `To exist/to have`, tags `l03-c1 l04-c2`. Stars are per Korean word.
- Decks are also read in Obsidian, so keep them plain markdown tables with no app-only columns.
- Never commit anything under `stats/`, or anything from the vault outside this folder.
- Keep the README short. Don't document what the UI already makes obvious.

## Commits

`type: summary`, lowercase, short, no period. Types: `init`, `feat`, `fix`, `refactor`, `docs`, `style`, `perf`, `test`, `build`, `chore`, `revert`. No `Co-Authored-By` trailer or Claude attribution.
