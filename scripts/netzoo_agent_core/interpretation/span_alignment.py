"""Locate a quote in a request that may be misspelled, without accepting a

different quote.

A quote had to appear in the request character for character. A request with a
transposed letter therefore made a correct quote impossible: the model writes
`regulator`, the user typed `regualtor`, and the reading -- which was right --
was thrown away. On a corpus containing misspelled requests every one of those
twelve trials lost its whole interpretation that way, and misspelling is the
single largest source of loss now measured.

The tempting fix is a similarity threshold over the whole quote. It cannot work.
`network` -> `regulatory network` is at least as similar as
`regualtor` -> `regulator`, so any threshold loose enough to rescue the typo also
admits a qualifier the user never wrote -- and that qualifier is exactly what
decides which capability is selected. Spelling and content are different axes and
one number cannot separate them.

So the quote is aligned to the request word by word, against a run of request
words of the same length, and every pair must correspond. Three constraints keep
that from becoming a similarity threshold in disguise; each is load-bearing:

- The distance allowed shrinks with the word. Four characters or fewer must
  match exactly, which is what stops `tf` from finding `of`.
- Two words that both mean something in this domain are never each other's
  typo. `mirna` and `mrna` are one edit apart and denote different molecules;
  nothing but this rule separates them.
- Only ASCII words are given any tolerance. Edit distance models a latin-script
  keyboard; `分組` and `分類` are also one edit apart and mean different things.

The result only ever adds alignments. A quote that appears verbatim aligns at
distance zero on every pair, so nothing that grounded before stops grounding.
"""

from __future__ import annotations

import re
from typing import get_args

from workflow_registry import (
    ArtifactType, EntityType, Granularity, OUTPUT_CAPABILITIES, Operation,
)

__all__: list[str] = []

_ASCII_WORD = re.compile(r"[a-z0-9]+")

#: Longest word length -> the largest edit distance still called a misspelling.
#: Short words are held to exact identity because at four characters or fewer
#: almost any other word is one edit away.
_TOLERANCE = ((4, 0), (7, 1))
_LONG_WORD_TOLERANCE = 2


def _registry_words() -> frozenset[str]:
    """Every word the registry's closed vocabulary is spelled out of."""
    literals = (
        *get_args(ArtifactType), *get_args(EntityType),
        *get_args(Operation), *get_args(Granularity),
        *(tag for capability in OUTPUT_CAPABILITIES.values()
          for tag in capability.selection_tags),
    )
    return frozenset(
        word for literal in literals for word in literal.split("_") if word
    )


#: Terms the registry does not contain whose conflation would still change the
#: answer. Each is within the tolerance of a registry word it does not mean:
#: `mrna`/`mirna` and `rna`/`tfa` are one edit apart, and a miRNA regulator and
#: an mRNA measurement select different capabilities. Kept explicit and short --
#: this list is a claim about biology, not about spelling, and every entry needs
#: a reason to be here.
_CONFUSABLE_NEIGHBOURS = frozenset({
    "mrna", "rna", "dna", "microrna", "ppi", "motif", "snp",
})

DOMAIN_WORDS: frozenset[str] = _registry_words() | _CONFUSABLE_NEIGHBOURS


def _tolerance(length: int) -> int:
    for limit, allowed in _TOLERANCE:
        if length <= limit:
            return allowed
    return _LONG_WORD_TOLERANCE


def _distance(left: str, right: str, limit: int) -> int:
    """Restricted Damerau-Levenshtein, stopped once it exceeds `limit`.

    Adjacent transposition counts as one edit rather than two: real
    misspellings are dominated by it, and every misspelling in the corpus that
    motivated this -- `regualtor`, `toosl`, `pateint`, `cohrot`, `standrad` --
    is exactly one transposition from its correct form.
    """
    if abs(len(left) - len(right)) > limit:
        return limit + 1
    previous: list[int] = []
    current = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        before_previous, previous, current = previous, current, [i]
        for j, right_char in enumerate(right, start=1):
            cost = 0 if left_char == right_char else 1
            best = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost)
            if (
                i > 1 and j > 1
                and left_char == right[j - 2] and left[i - 2] == right_char
            ):
                best = min(best, before_previous[j - 2] + 1)
            current.append(best)
        if min(current) > limit:
            return limit + 1
    return current[-1]


def _aligns(quoted: str, requested: str) -> bool:
    """Whether one quoted word is the same word as one word of the request."""
    if quoted == requested:
        return True
    if not (_ASCII_WORD.fullmatch(quoted) and _ASCII_WORD.fullmatch(requested)):
        return False
    if quoted in DOMAIN_WORDS and requested in DOMAIN_WORDS:
        return False
    limit = _tolerance(max(len(quoted), len(requested)))
    return limit > 0 and _distance(quoted, requested, limit) <= limit


def aligned_span(span: str, task: str) -> bool:
    """Whether `span` names a run of words in `task`, allowing for misspelling.

    Both arguments are already normalized to lowercase space-separated words.
    """
    quoted, requested = span.split(), task.split()
    if not quoted or len(quoted) > len(requested):
        return False
    return any(
        all(
            _aligns(quoted_word, requested[start + offset])
            for offset, quoted_word in enumerate(quoted)
        )
        for start in range(len(requested) - len(quoted) + 1)
    )
