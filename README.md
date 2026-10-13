# eas211-korean-trainer

Flashcard and typing drills for Korean vocab. Words live in markdown decks under `decks/`. Progress is saved to `stats/`, which git ignores, so a fresh clone starts clean.

## Run

```
uv sync
uv run app.py
```

Opens localhost:8520 with `decks/eas211/vocab.md`. Options: `--deck path/to/deck.md`, `--port N`.

## Decks

One markdown table per deck. `tags` are space-separated and become the sets you pick from. `notes` is an optional hint shown with the answer. The app never writes decks, so you can edit them while it runs.

```
| korean | english | tags | notes |
| --- | --- | --- | --- |
| 노래 | Song | l04-c1 | 노래하다 = to sing |
```

## Stats

`decks/<course>/<name>.md` saves to `stats/<course>/<name>.json`, keyed by korean + english. Editing tags or notes keeps a word's history. Editing the korean or english resets it.

Score (0–100) = 40% ko→en accuracy + 40% en→ko accuracy + 20% streak (0–5). Accuracy is smoothed as (correct+1)/(attempts+2), so it starts near 50%.
