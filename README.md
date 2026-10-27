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

## Conjugations

If the deck folder has a `conjugations.md`, you can switch Study to Conjugations. Learn shows one verb with all its forms, grouped by rule. Flashcards and Typing show the dictionary form and a target form (e.g. `춥다` + `아/어요`). Pick forms and rules (ㅂ irregular, ㄹ stem, ...) to narrow it down. The word list shows your accuracy per rule and per form.

```
| korean | english | tags | pos | rule | 아/어요 | 지요 | (으)러 가요 | 고 싶어요 |
```

Every column after `rule` is a form. `nan` = the form doesn't exist for that word. 고 싶어해요 is derived from 고 싶어요, and typing accepts 죠 for 지요.

## Numbers

Switch Study to Numbers and pick a category: Sino-Korean (0 to 99,999,999), Native (1 to 99), Counting (두 병), Time, Age, Dates, Price, Phone, or Mixed. Then pick a mode and a direction (123 or English → 한, 한 → 123 or English, or mixed). Nothing is saved.

## Stats

`decks/<course>/<name>.md` saves to `stats/<course>/<name>.json`, keyed by korean + english. Editing tags or notes keeps a word's history. Editing the korean or english resets it.

Score (0–100) = 40% ko→en accuracy + 40% en→ko accuracy + 20% streak (0–5). Accuracy is smoothed as (correct+1)/(attempts+2), so it starts near 50%.
