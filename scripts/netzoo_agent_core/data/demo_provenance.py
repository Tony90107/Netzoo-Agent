"""Cryptographic provenance for version-controlled demonstration datasets."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path

from ..settings import PROJECT_ROOT

__all__: list[str] = []

_AUTHORITY_NOTE = (
    "Bundled demo provenance: every input matched its registered path and SHA-256 "
    "digest; unresolved synthetic labels are accepted for demonstration only and "
    "are not biological evidence."
)

_LIONESS_PANDA = {
    "expression_file": (
        "data/lioness-toy/expression.tsv",
        "5b0fbca0b64ee2c27db7e8481e08dde6b91e104d0a1ec30cd7d2ec7208ff8721",
    ),
    "motif_file": (
        "data/lioness-toy/motif-panda.tsv",
        "b31ae49e467e514ae206def47ed7aa82a066634767b09c73aca110794f25442c",
    ),
    "ppi_file": (
        "data/lioness-toy/ppi.tsv",
        "bdbda375e9e037e182918a674a4f7221067c37d78cbc9fe409d720af9e1dba13",
    ),
}

_LIONESS_PUMA = {
    "expression_file": _LIONESS_PANDA["expression_file"],
    "motif_file": (
        "data/lioness-toy/prior-puma.tsv",
        "6d55b149d5765e502d28cf3a92a9c1b800bb7e5d85f02838a4235d48cf60d131",
    ),
    "ppi_file": _LIONESS_PANDA["ppi_file"],
    "mirna_file": (
        "data/lioness-toy/mirna.txt",
        "c8c63fca3d443069bca0a8683f22119b691e9f7ba39526eb8a9ee1f2c05b29ef",
    ),
}

_OFFICIAL_PANDA = {
    "expression_file": (
        "data/official-toy/ToyExpressionData.txt",
        "b77a8ad478f9e35bb2219ad47b01119f2d29344caf1551c7644ade20e6d4e2c2",
    ),
    "motif_file": (
        "data/official-toy/ToyMotifData.txt",
        "557c4007a55d3e3e3cc7b886255a75b75d137e82f3f4c12b36eb4785c7838fac",
    ),
    "ppi_file": (
        "data/official-toy/ToyPPIData.txt",
        "772e423899424bfe60b8836f629e8ae4589caff71fc8f167b86a5932566ba861",
    ),
}

_OFFICIAL_PUMA = {
    **_OFFICIAL_PANDA,
    "mirna_file": (
        "data/official-toy/ToyMiRList.txt",
        "deb1dd1f05cd70615eaaee710bc6c8cf73c9bf0dee99b37881f9ce54d5bfab77",
    ),
}

_COBRA = {
    "expression_file": (
        "data/cobra-toy/expression.tsv",
        "7e75b5a47915dc5c9485c7d41cba02b69ae63bd426c7bfe3afa6ccda7142245f",
    ),
    "design_file": (
        "data/cobra-toy/design.tsv",
        "ef715c4c45cb8886ae5302ca60bffcbd15ef2b75b9f5d2f5b4d578bf3c774ee4",
    ),
}

_LIONESS_COEXPRESSION = {
    "expression_file": _LIONESS_PANDA["expression_file"],
}

_BUNDLED_DEMOS: dict[str, tuple[dict[str, tuple[str, str]], ...]] = {
    "run_panda": (_OFFICIAL_PANDA, _LIONESS_PANDA),
    "run_puma": (_OFFICIAL_PUMA, _LIONESS_PUMA),
    "run_lioness_panda": (_LIONESS_PANDA,),
    "run_lioness_puma": (_LIONESS_PUMA,),
    "run_lioness_coexpression": (_LIONESS_COEXPRESSION,),
    "run_cobra": (_COBRA,),
}


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _resolved(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve(strict=True)


def _matches_bundle(
    inputs: Mapping[str, str],
    bundle: Mapping[str, tuple[str, str]],
) -> bool:
    try:
        for field_name, (relative_path, expected_digest) in bundle.items():
            value = inputs.get(field_name, "")
            if not value:
                return False
            expected = (PROJECT_ROOT / relative_path).resolve(strict=True)
            observed = _resolved(value)
            if observed != expected or not observed.is_file():
                return False
            if _digest(observed) != expected_digest:
                return False
    except (OSError, RuntimeError):
        return False
    return True


def is_verified_bundled_demo(action: str, inputs: Mapping[str, str]) -> bool:
    """Return true only for an exact registered bundle whose bytes still match."""

    bundles = (
        tuple(bundle for choices in _BUNDLED_DEMOS.values() for bundle in choices)
        if action == "inspect_inputs"
        else _BUNDLED_DEMOS.get(action, ())
    )
    return any(_matches_bundle(inputs, bundle) for bundle in bundles)


def bundled_demo_authority_note() -> str:
    """Explain why a bundled demo may bypass remote gene authority lookup."""

    return _AUTHORITY_NOTE
