# eas211-korean-trainer

NiceGUI app for drilling Korean vocab from markdown decks. Public repo, lives inside an Obsidian vault.

## Layout

- `app.py`: UI (setup, learn, flashcards, typing). `--deck`, `--port`.
- `session.py`: word selection, weighted order, requeueing misses.
- `checking.py`: lenient typed-answer matching. `uv run python checking.py` runs its self-tests.
- `vocab_io.py`: reads decks, reads/writes stats.
- `decks/<course>/<name>.md`: tracked. Columns `korean | english | tags | notes` only.
- `stats/<course>/<name>.json`: gitignored, per-user progress.

## Rules

- The app never writes decks. All progress goes to `stats/`.
- Stats are keyed by `korean\tenglish`. Changing either field orphans that word's stats.
- Decks are also read in Obsidian, so keep them plain markdown tables with no app-only columns.
- Never commit anything under `stats/`, or anything from the vault outside this folder.
- Keep the README short. Don't document what the UI already makes obvious.

## Commits

`type: summary`, lowercase, short, no period. Types: `init`, `feat`, `fix`, `refactor`, `docs`, `style`, `perf`, `test`, `build`, `chore`, `revert`. No `Co-Authored-By` trailer or Claude attribution.
