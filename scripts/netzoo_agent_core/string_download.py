"""Typed STRING bulk-network acquisition from the official download host."""

from __future__ import annotations

import gzip
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote

from .acquisition_intent import acquisition_request_excluded, explicit_acquisition_request
from . import settings
from .contracts import RequestedOutcome, TaskDecision, tool
from .data.paths import _resolve_user_path

if TYPE_CHECKING:
    from .contracts.outcomes import SemanticInterpretation

STRING_VERSION = "12.5"
NETWORK_KINDS = {
    "functional": "protein.links",
    "physical": "protein.physical.links",
    "regulatory": "protein.regulatory.links",
}
SPECIES_URL = f"https://stringdb-downloads.org/download/species.v{STRING_VERSION}.txt"
_ALIASES = {
    "human": "9606", "humans": "9606", "homo sapiens": "9606", "人類": "9606",
    "mouse": "10090", "mice": "10090", "mus musculus": "10090", "小鼠": "10090",
    "rat": "10116", "rattus norvegicus": "10116", "大鼠": "10116",
    "saccharomyces cerevisiae": "4932",
}


def string_download_requested(task: str, interpretation: SemanticInterpretation) -> bool:
    """Require both semantic acquisition intent and an explicit STRING source."""
    if interpretation.request_mode != "execute":
        return False
    if acquisition_request_excluded(task):
        return False
    clear_download = explicit_acquisition_request(task)
    if not re.search(r"(?<![A-Za-z0-9])STRING(?:-DB)?(?![A-Za-z0-9])|string-db\.org", task, re.I):
        return False
    if re.search(
        r"\b(?:protein[.\s]+(?:sequences?|info)|aliases|embeddings?|homology|orthology|enrichment|species[.\s]+(?:list|catalog|tree)|regulatory[.\s]+events)\b"
        r"|序列|別名|别名|嵌入|同源|富集|物種清單|物种清单|蛋白質資訊|蛋白质信息",
        task, re.I,
    ):
        return False
    hypotheses = interpretation.outcome_hypotheses
    return bool(hypotheses) and (
        all(item.outcome.operation == "acquire" for item in hypotheses)
        or clear_download
    )


def requested_network_kind(task: str) -> str | None:
    explicit = re.search(r"\bstring_network_type\s*(?:=|:|is)\s*(functional|physical|regulatory)\b", task, re.I)
    if explicit:
        return explicit.group(1).lower()
    patterns = {
        "regulatory": r"regulat(?:ory|ion)|調控|调控",
        "physical": r"physical|protein.protein interaction|物理|實體互作|实体互作",
        "functional": r"functional|association|一般.*網路|一般.*网络|功能性|關聯網路|关联网络",
    }
    matches = [kind for kind, pattern in patterns.items() if re.search(pattern, task, re.I)]
    return matches[0] if len(matches) == 1 else None


def requested_species(task: str) -> str | None:
    marked = re.search(
        r"(?:\b(?:taxon|species|organism)|物種)\s*(?:=|:|is|是)\s*([^;；\n]+)[;；]",
        task, re.I,
    )
    if marked:
        return marked.group(1).strip().strip("'\"") or None
    explicit_match = re.search(
        r"\b(?:taxon|species|organism)\s*(?:=|:|is)\s*"
        r"([A-Za-z0-9_-]+(?:\s+[A-Za-z][A-Za-z0-9_-]+)?)",
        task, re.I,
    )
    explicit = explicit_match.group(1) if explicit_match else None
    if explicit:
        return explicit
    taxid = re.search(r"\b(?:taxid|taxon|species)\s*(?:=|:|is)?\s*(\d{3,8})\b", task, re.I)
    if taxid:
        return taxid.group(1)
    # Alias matching is parameter extraction only. The semantic interpreter
    # above, not this vocabulary, decides whether acquisition was requested.
    matches = [
        name for name in _ALIASES
        if (name in task if not name.isascii()
            else bool(re.search(rf"(?<!\w){re.escape(name)}(?!\w)", task, re.I)))
    ]
    taxids = {_ALIASES[name] for name in matches}
    return next(iter(taxids)) if len(taxids) == 1 else None


def string_download_decision(task: str, interpretation: SemanticInterpretation) -> TaskDecision | None:
    if not string_download_requested(task, interpretation):
        return None
    hypotheses = interpretation.outcome_hypotheses
    if not all(item.outcome.operation == "acquire" for item in hypotheses):
        # The user's explicit download command resolves a contradictory model
        # reading. Discard the model's inferred operation and its evidence.
        corrected = hypotheses[0].outcome.model_copy(update={"operation": "acquire"})
        requested_hypotheses = [hypotheses[0].model_copy(update={
            "outcome": corrected, "evidence": [],
        })]
    else:
        requested_hypotheses = hypotheses
    return TaskDecision(
        action="download_string", in_scope=True, should_execute=True,
        intent_type="prepare_input",
        confidence=min(item.confidence for item in requested_hypotheses),
        reason="Download an existing STRING species network from the official bulk-data host.",
        requested_outcome=requested_hypotheses[0].outcome,
        outcome_hypotheses=requested_hypotheses,
        capability_match_status="exact",
        match_basis=("semantic" if requested_hypotheses is hypotheses else "semantic_validation_recovery"),
        matched_actions=["download_string"],
        taxon=requested_species(task), string_network_type=requested_network_kind(task),
        output_dir=_explicit_output_dir(task) or "data/string",
    )


def continued_string_download_decision(task: str) -> TaskDecision | None:
    """Restore only the wizard's explicit acquisition fields on its next turn."""
    if not re.search(r"\bPREVIOUS_ACTION=download_string\b", task) or not re.search(r"\bDownload\s+(?:the\s+existing\s+)?STRING\b", task, re.I):
        return None
    return TaskDecision(
        action="download_string", in_scope=True, should_execute=True,
        intent_type="prepare_input", confidence=1.0,
        reason="Continue the explicit STRING data acquisition request.",
        requested_outcome=RequestedOutcome(operation="acquire", artifact_type="unknown", granularity="unknown"),
        capability_match_status="exact", match_basis="confirmed_context",
        matched_actions=["download_string"],
        taxon=requested_species(task), string_network_type=requested_network_kind(task),
        output_dir=_explicit_output_dir(task) or "data/string",
    )


def _explicit_output_dir(task: str) -> str | None:
    match = re.search(r"\boutput_dir\s*=\s*([^\s;,。]+)", task, re.I)
    return match.group(1).rstrip(".") if match else None


def _taxid(species: str) -> str | None:
    clean = species.strip().casefold()
    return clean if re.fullmatch(r"\d{3,8}", clean) else _ALIASES.get(clean)


def _resolve_species(species: str) -> str:
    known = _taxid(species)
    if known:
        return known
    result = subprocess.run(
        ["curl", "--fail", "--silent", "--show-error", "--location",
         "--proto", "=https", "--proto-redir", "=https", "--max-time", "45",
         "--max-filesize", "3000000", SPECIES_URL],
        capture_output=True, text=True, timeout=55, check=False,
    )
    if result.returncode:
        raise ValueError("STRING species catalog lookup failed; enter an NCBI taxonomy ID or retry later.")
    sought = species.strip().casefold()
    matches = []
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if not fields or not re.fullmatch(r"\d{3,8}", fields[0]):
            continue
        if any(field.strip().casefold() == sought for field in fields[1:]):
            matches.append(fields[0])
    if len(set(matches)) != 1:
        raise ValueError("STRING species name was not uniquely found; enter the NCBI taxonomy ID.")
    return matches[0]


def _filename(taxid: str, kind: str) -> str:
    return f"{taxid}.{NETWORK_KINDS[kind]}.v{STRING_VERSION}.txt.gz"


def _download_url(taxid: str, kind: str) -> str:
    stem = f"{NETWORK_KINDS[kind]}.v{STRING_VERSION}"
    return f"https://stringdb-downloads.org/download/{quote(stem)}/{quote(_filename(taxid, kind))}"


def _existing_file(filename: str, output_dir: Path) -> Path | None:
    project_root = settings.PROJECT_ROOT
    roots = dict.fromkeys((output_dir, project_root / "data", project_root / "outputs"))
    for root in roots:
        if not root.is_dir():
            continue
        direct = root / filename
        if direct.is_file() and not direct.is_symlink():
            return direct
        if root == output_dir:
            continue
        for candidate in root.rglob(filename):
            if candidate.is_file() and not candidate.is_symlink():
                return candidate
    return None


def _validate_gzip(path: Path, taxid: str) -> None:
    with gzip.open(path, "rt", encoding="utf-8") as source:
        header = source.readline().strip().split()
        if len(header) < 3 or header[:2] != ["protein1", "protein2"]:
            raise ValueError("Downloaded file is not a STRING protein links table.")
        first = source.readline().strip().split()
        if len(first) < 3 or not first[0].startswith(taxid + "."):
            raise ValueError("Downloaded STRING file has no links for the requested species.")
        for _ in source:
            pass  # Consume the stream to verify gzip CRC and truncation.


def _existing_report(path: Path, taxid: str) -> str:
    try:
        _validate_gzip(path, taxid)
    except (OSError, ValueError, UnicodeError, EOFError) as error:
        return (
            f"Error: A file named {path.name} exists at {path}, but it is not a valid "
            f"STRING links archive ({error}). Move or repair it before retrying."
        )
    return f"STRING file already exists locally: {path}. No repeat download is needed."


@tool
def download_string(taxon: str, string_network_type: str, output_dir: str = "data/string") -> str:
    """Download one STRING species network using curl, without overwriting local data."""
    if string_network_type not in NETWORK_KINDS or not taxon.strip():
        return "Error: Specify a species and one network type: functional, physical, or regulatory."
    destination = _resolve_user_path(output_dir or "data/string")
    known_taxid = _taxid(taxon)
    if known_taxid:
        filename = _filename(known_taxid, string_network_type)
        if existing := _existing_file(filename, destination):
            return _existing_report(existing, known_taxid)
    if not settings.EXECUTE_TOOLS:
        source = (_download_url(known_taxid, string_network_type)
                  if known_taxid else f"{SPECIES_URL} (resolve species, then select {string_network_type} links)")
        return (
            "Dry run only; no file was downloaded.\n"
            f"Species: {taxon}\nNetwork: {string_network_type}\n"
            f"Destination: {destination}\nOfficial source: {source}\n"
            "Enter /execute to run the approved download."
        )
    try:
        taxid = _resolve_species(taxon)
        filename = _filename(taxid, string_network_type)
        if existing := _existing_file(filename, destination):
            return _existing_report(existing, taxid)
        destination.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".string-download-", suffix=".part", dir=destination)
        os.close(fd)
        temporary_path = Path(temporary)
        try:
            command = [
                "curl", "--fail", "--silent", "--show-error", "--location",
                "--proto", "=https", "--proto-redir", "=https", "--max-time", "1800",
                "--retry", "2", "--output", str(temporary_path),
                _download_url(taxid, string_network_type),
            ]
            result = subprocess.run(command, capture_output=True, text=True, timeout=1810, check=False)
            if result.returncode:
                return f"Error: STRING download failed (curl exit {result.returncode}): {result.stderr.strip()[:300]}"
            _validate_gzip(temporary_path, taxid)
            final_path = destination / filename
            try:
                os.link(temporary_path, final_path)
            except FileExistsError:
                return _existing_report(final_path, taxid)
            return f"Downloaded STRING {string_network_type} network for taxon {taxid}: {final_path} ({final_path.stat().st_size} bytes)."
        finally:
            temporary_path.unlink(missing_ok=True)
    except (OSError, subprocess.TimeoutExpired, ValueError, UnicodeError, EOFError) as error:
        return f"Error: STRING download could not be completed: {error}"
