from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import settings  # noqa: E402
from netzoo_agent_core.contracts import GeneLabelSuggestions  # noqa: E402
from netzoo_agent_core.data.gene_repair_hints import (  # noqa: E402
    suggest_gene_corrections,
)
from netzoo_agent_core.data.gene_validation import (  # noqa: E402
    GeneCache,
    GeneRecord,
)


class FakeSuggester:
    def __init__(self, suggestions):
        self.suggestions = suggestions
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return GeneLabelSuggestions(suggestions=self.suggestions)


def _seed(cache_path, *symbols):
    GeneCache(cache_path).upsert(
        [
            GeneRecord(
                identifier=symbol,
                normalized_identifier=symbol.casefold(),
                namespace="symbol_like",
                canonical_id=f"ncbi_gene:{index}",
                symbol=symbol,
                taxon="human",
                status="valid",
                authority="NCBI Gene",
                source="test",
            )
            for index, symbol in enumerate(symbols, start=1)
        ]
    )


def test_a_suggestion_the_authority_confirms_is_offered(tmp_path, monkeypatch):
    cache_path = tmp_path / "gene.sqlite3"
    _seed(cache_path, "MDM2")
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(cache_path))
    mapper = FakeSuggester(
        [{"label": "MDM7", "likely_symbol": "MDM2", "reason": "Likely a typo."}]
    )

    assert suggest_gene_corrections(["MDM7"], "human", mapper) == [
        ("MDM7", "MDM2", "Likely a typo.")
    ]


def test_a_hallucinated_suggestion_is_dropped(tmp_path, monkeypatch):
    """The model's own claim that a symbol exists is never taken at its word."""
    cache_path = tmp_path / "gene.sqlite3"
    _seed(cache_path, "MDM2")
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(cache_path))
    monkeypatch.setenv("NETZOO_GENE_ONLINE_LOOKUP", "off")
    mapper = FakeSuggester(
        [{"label": "CCND8", "likely_symbol": "CCND9", "reason": "Likely a typo."}]
    )

    [(label, symbol, reason)] = suggest_gene_corrections(["CCND8"], "human", mapper)
    assert label == "CCND8"
    assert symbol == ""
    assert reason == "Likely a typo."


def test_a_suggestion_for_a_label_that_was_not_asked_about_is_ignored(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(tmp_path / "gene.sqlite3"))
    mapper = FakeSuggester(
        [{"label": "SOMETHING_ELSE", "likely_symbol": "TP53", "reason": "x"}]
    )

    assert suggest_gene_corrections(["MDM7"], "human", mapper) == []


def test_no_hint_is_produced_without_a_model(tmp_path, monkeypatch):
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(tmp_path / "gene.sqlite3"))
    assert suggest_gene_corrections(["MDM7"], "human", None) == []


def test_synthetic_test_mode_does_not_pay_for_hints(tmp_path, monkeypatch):
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(tmp_path / "gene.sqlite3"))
    monkeypatch.setattr(settings, "TEST_DATA_MODE", True)
    mapper = FakeSuggester(
        [{"label": "MDM7", "likely_symbol": "MDM2", "reason": "Likely a typo."}]
    )

    assert suggest_gene_corrections(["MDM7"], "human", mapper) == []
    assert mapper.calls == []


def test_a_model_failure_is_silent(tmp_path, monkeypatch):
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(tmp_path / "gene.sqlite3"))

    class Broken:
        def invoke(self, messages):
            raise RuntimeError("provider down")

    assert suggest_gene_corrections(["MDM7"], "human", Broken()) == []


def test_the_labels_are_read_back_from_the_preflight_errors():
    from netzoo_agent_core.planning.evidence import _unrecognized_labels
    from netzoo_agent_core.data.gene_validation import UNRECOGNIZED_PHRASE

    errors = [
        f"PANDA/PUMA inputs: error: expression genes {UNRECOGNIZED_PHRASE}MDM7, RB7",
        f"motif regulator genes: {UNRECOGNIZED_PHRASE}E2F9",
        "expression: values must be numeric; numeric cell ratio is 50.0%.",
    ]

    assert _unrecognized_labels(errors) == ["MDM7", "RB7", "E2F9"]


@pytest.mark.parametrize("errors", [[], ["expression: values must be numeric."]])
def test_a_failure_with_no_rejected_label_asks_no_model(errors):
    from netzoo_agent_core.planning.evidence import _gene_repair_hints

    mapper = FakeSuggester([])
    assert _gene_repair_hints(errors, "human", mapper) == []
    assert mapper.calls == []
