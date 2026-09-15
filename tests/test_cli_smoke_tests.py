from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.cli import smoke_tests  # noqa: E402


def _write_fixtures(root: Path) -> None:
    for directory in ("data/auto-check-valid", "data/auto-check-invalid"):
        fixture_dir = root / directory
        fixture_dir.mkdir(parents=True)
        for name in ("expression.tsv", "motif.tsv", "ppi.tsv"):
            (fixture_dir / name).write_text("fixture\n", encoding="utf-8")


def test_smoke_runner_reports_authority_and_lookup_diagnostics(monkeypatch, tmp_path):
    _write_fixtures(tmp_path)
    monkeypatch.setattr(smoke_tests, "PROJECT_ROOT", tmp_path)

    valid_report = """
  note: expression genes authority validation for taxon 'Homo sapiens': 2 valid (2 cache hit(s)).
    - id: ENSG00000141510; status: valid; canonical_id: ensembl_gene:ENSG00000141510; authority: Ensembl; source: cache; taxon: Homo sapiens; symbol: TP53
    - id: ENSG00000012048; status: valid; canonical_id: ensembl_gene:ENSG00000012048; authority: Ensembl; source: cache; taxon: Homo sapiens; symbol: BRCA1
"""
    invalid_report = """
  note: expression genes authority validation for taxon 'Homo sapiens': 1 invalid (1 online lookup batch(es)).
    - id: ENSG00000999999; status: invalid; canonical_id: (none); authority: Ensembl; source: ensembl_rest; taxon: Homo sapiens; symbol: (none)
  error: expression genes not recognized by the configured gene authority: ENSG00000999999
"""

    def fake_inspect(*, expression_file, **_kwargs):
        if "invalid" in expression_file:
            return invalid_report, False, False
        return valid_report, True, False

    monkeypatch.setattr(smoke_tests, "_inspect_panda_inputs_impl", fake_inspect)

    output = smoke_tests.run_smoke_tests()

    assert "valid fixtures: PASS" in output
    assert "invalid fixtures: PASS" in output
    assert "cache_hits: 2; online_queries: 0" in output
    assert "cache_hits: 0; online_queries: 1" in output
    assert "authorities: Ensembl" in output
    assert "sources: cache" in output
    assert "Overall: PASS" in output
