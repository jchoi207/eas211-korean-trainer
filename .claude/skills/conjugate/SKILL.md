---
name: conjugate
description: Add a verb/adjective to the conjugation table, or add a new form (tense/ending) column. Use when Jonathan says "add 먹다", "add the past tense", "conjugate the new words", etc.
---

# Conjugate

Table: `decks/<course>/conjugations.md`. Word list: `decks/<course>/vocab.md`.

Columns: `korean | english | tags | pos | rule | <form> | <form> ...`. Every column after `rule` is a form, headed by its ending as taught (e.g. `아/어요`, `(으)러 가요`).

## Add a verb or adjective

1. If it's not in `vocab.md`, add it there first (`korean | english | tags | notes`). `korean`, `english`, `tags` in the conjugation row must match the vocab row exactly.
2. `pos`: `verb` or `adj`. 있다 is `verb`, 없다 is `adj`.
3. `rule`: one of `받침`, `vowel stem`, `하다`, `ㄹ stem`, `ㅂ irregular`, `ㄷ irregular`, `르 irregular`, `ㅡ drop`, `honorific`. Add a new label only for a genuinely new class (e.g. `ㅅ irregular`, `ㅎ irregular`).
4. Fill every form column. For multi-word entries (장 보다, 사진 찍다) conjugate the last word and keep the rest.
5. Verify (below), then append in lesson order.

## Add a form

1. Use only forms Jonathan says he learned. Ask for the exact ending as taught if unclear.
2. Add the column after the last form column, header = the ending.
3. Fill it for every row, with `nan` where it doesn't exist. Decide per form which stems change and which `pos` it allows, and state that in one line in the table's note at the top.
4. If the app needs a form-specific checking rule, mention it rather than editing the app here.

## nan policy

`nan` when the form is ungrammatical or meaningless for that word:
- (으)러 가요, 고 싶어요, and other intent/desire forms: not with `adj`.
- (으)러 가요: not with motion verbs (가다, 오다, 다니다, 여행가다).
- Honorifics (계시다): not with first-person forms like 고 싶어요.

Grammatical but context-dependent forms (살러 가요) stay filled. Flag them to Jonathan.

## Verify

- Look up every word that isn't `받침`/`vowel stem`/`하다`, and any word whose class is unclear: `https://en.wiktionary.org/wiki/<word>` gives a conjugation table and the irregular class (e.g. "ㅂ-irregular"). Same spelling can be two words (묻다 "ask" is ㄷ-irregular, 물어요; 묻다 "bury" is regular, 묻어요), so match the sense.
- If Wiktionary lacks the word, ask Jonathan to check 표준국어대사전 (stdict.korean.go.kr, entry page shows 활용 like `[추우니, 추워]`). Its search results page doesn't show 활용, so it can't be fetched directly.
- Optional second opinion: KoParadigm (`pip install koparadigm`, takes the stem, e.g. `춥`). Known wrong: ㄹ stem + 러 (gives 사러 for 살다, should be 살러), honorifics (계시어요 vs 계세요), and its verb/adjective labels. Never copy its output without checking.
- Never guess. If unsure, leave the cell blank and ask.

## Rules reference (forms learned so far)

- 아/어요: last stem vowel ㅏ/ㅗ → 아요, else 어요. 하다 → 해요. Contract: ㅗ+아 → ㅘ (봐요), ㅜ+어 → ㅝ (줘요), ㅣ+어 → ㅕ (마셔요), ㅏ/ㅐ/ㅓ absorb (가요, 보내요). ㅡ drops (커요, 나빠요). ㅂ → 우 + 어요 (추워요). ㄷ → ㄹ before vowel (들어요). 르 → ㄹㄹ (빨라요). 계시다 → 계세요.
- 지요: stem + 지요, no changes.
- (으)러 가요: 받침 → 으러, vowel stem or ㄹ stem → 러 (놀러). ㄷ irregular → 들으러.
- 고 싶어요: stem + 고 싶어요, no changes. 3rd person: 고 싶어해요 (derived, no column).
