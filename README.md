# trainer

Flashcard and typing drills for Korean vocab. Words live in markdown decks under `decks/`. Your progress is saved separately in `stats/`, which git ignores, so a fresh clone starts with clean stats.

## Setup and run

```
uv sync
uv run app.py
```

This opens localhost:8520 with `decks/eas211/vocab.md`. Use `--deck path/to/deck.md` for a different deck, or `--port` if 8520 is taken. Avoid 8080, which has dropped the live connection on some machines.

## Using it

- Sets: pick one or more tags (their union), or "all".
- Direction: 한 → EN, EN → 한, or mixed. You can switch mid-session. Hidden in learn mode.
- Mode: learn (Korean and English side by side in file order, ← → or Space to move, nothing graded or saved), flashcards (Space flips, ← missed, → got it) or typing (Enter checks, Enter again moves on). "I was right" overrides a wrong verdict.
- Words: all words in the selected sets, or the worst N by miss rate in the chosen direction. Untested words rank last.
- A missed word comes back about 3 cards later. The session ends when every word has been answered correctly once.
- Word list: the table for the selected sets, weakest first, with the score column shaded red to green.

Typing is lenient. It ignores case, spaces in Korean, and trailing `?.!`. It also accepts any part split by `/ , ;`, the text with or without its parentheses, and answers with or without a leading "to" or "please".

## Decks

A deck is a markdown file with one table. To add a word, add a row with `korean`, `english` and `tags` (space-separated, e.g. `l02-c1 country`). `notes` is an optional hint shown with the answer. The app only reads decks, so it's safe to edit them (in Obsidian, for example) while it's running.

```
| korean | english | tags | notes |
| --- | --- | --- | --- |
| 노래 | Song | l04-c1 | 노래하다 = to sing |
```

## Stats

Stats for `decks/<course>/<name>.md` go in `stats/<course>/<name>.json` (`stats/<name>.json` for a deck outside `decks/`). They are keyed by korean + english, so changing a word's tags or notes keeps its history, but changing either the korean or english starts it fresh.

| field | meaning |
| --- | --- |
| ko→en, en→ko | correct/attempts per direction |
| box | streak level 0–5: +1 per correct answer, back to 0 on a miss |
| score | 0–100 mastery, blank until tested (computed, not stored) |
| last | date last reviewed |

Score = 40% ko→en accuracy + 40% en→ko accuracy + 20% box/5. Each accuracy is smoothed as (correct+1)/(attempts+2), so it starts near 50% and needs repeated answers to move. An untested direction counts as 50%.
