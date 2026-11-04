"""Shared UI constants and snippets."""

from trainer.data import vocab

DIRECTIONS = {"ko→en": "한 → EN", "en→ko": "EN → 한", "mixed": "Mixed"}
DIRECTION_HINT = {"ko→en": "Korean → English", "en→ko": "English → Korean"}
STUDY = {"words": "Words", "conj": "Conjugations", "numbers": "Numbers"}
MODES = {"learn": "Learn", "flash": "Flashcards", "type": "Typing"}
POOLS = {"all": "All", "worst": "Worst", "starred": "Starred"}
# Score cell tinted red (0) -> amber -> green (100); blank when untested.
SCORE_CELL = """
<q-td :props="props" :style="props.value == null ? '' : `background: hsla(${props.value * 1.2}, 75%, 50%, 0.35)`">
  {{ props.value }}
</q-td>
"""


def columns(names: list[str]) -> list[dict]:
    return [{"name": c, "label": c, "field": c, "sortable": True, "align": "left"} for c in names]


TABLE_COLUMNS = columns(["star"] + vocab.COLUMNS)
CONJ_COLUMNS = columns(["star", "korean", "form", "answer", "rule", "correct", "box", "score", "last"])
STAR_CELL = """
<q-td :props="props">
  <q-btn flat dense round size="sm" :icon="props.value ? 'star' : 'star_border'" :color="props.value ? 'amber' : 'grey'"
         @click="() => $parent.$emit('star', props.row.korean)" />
</q-td>
"""

# Emit the input's DOM value on Enter. If the Enter only commits a Hangul
# syllable (IME still composing), wait for the composition to finish first.
ENTER_JS = """(e) => {
  const send = () => emit(e.target.value);
  if (e.isComposing) e.target.addEventListener('compositionend', () => setTimeout(send, 0), {once: true});
  else send();
}"""
