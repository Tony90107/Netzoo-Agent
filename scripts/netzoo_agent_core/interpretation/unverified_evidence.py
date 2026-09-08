"""What to do with a reading whose quotes are not in the request.

The evidence contract used to have one answer: discard the whole interpretation.
Across 35 live rounds that answer cost 148 of the 188 entries in this family
their entire run, and a round on a corpus containing misspelled requests lost
every one of its twelve misspelled trials that way -- while the reading itself
was usually right. A request with a transposed letter makes a matching quote
impossible; it does not make the meaning unclear.

So the reading is kept, and everything that would let it pass for a verified one
is taken away. This module owns that trade, which is the only place in the
pipeline where a safety property is deliberately relaxed, and states its whole
extent in one file:

- the reading's stated confidence is reduced;
- it can never present itself as an exact capability match;
- it can never authorize an action.

What it does NOT do is stop detecting the problem. Every `ungrounded_evidence`
issue is still raised, still recorded, and still shown to the user. A quote that
adds a qualifier the request never contained is caught exactly as before; what
changed is what happens next. The relaxation cannot distinguish a typo from an
invention -- both are a quote the request does not contain -- and the bounds
above are what contain the second case.
"""

from __future__ import annotations

from ..contracts.outcomes import CapabilityMatch, SemanticInterpretation

__all__: list[str] = []

#: Applied to every hypothesis of a reading kept this way. Multiplicative rather
#: than a cap: the matcher ranks on `(evidence_score, confidence, specificity)`,
#: so scaling every hypothesis by one factor cannot reorder them, while a cap
#: would collapse distinct hypotheses into invented ties.
CONFIDENCE_FACTOR = 0.5

UNVERIFIED_BASIS = "unverified_evidence"


def with_reduced_confidence(
    interpretation: SemanticInterpretation,
) -> SemanticInterpretation:
    """Lower every hypothesis's stated confidence, changing nothing else."""
    return interpretation.model_copy(update={
        "outcome_hypotheses": [
            hypothesis.model_copy(update={
                "confidence": hypothesis.confidence * CONFIDENCE_FACTOR,
            })
            for hypothesis in interpretation.outcome_hypotheses
        ],
    })


def bounded_match(match: CapabilityMatch) -> CapabilityMatch:
    """Hold an unverified reading below an exact match, keeping its candidates.

    A candidate the user can read and judge is the point of keeping the reading
    at all; calling it exact is what the missing quote does not support.
    """
    return match.model_copy(update={
        "status": "fallback" if match.status == "exact" else match.status,
        "match_basis": UNVERIFIED_BASIS,
    })
