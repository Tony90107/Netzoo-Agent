"""Shared, strict table parsing for validation and runtime wrappers."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ANNOTATION_KEYS = {
    "annotation",
    "annotations",
    "comment",
    "comments",
    "created",
    "date",
    "description",
    "file",
    "metadata",
    "note",
    "notes",
}


@dataclass(frozen=True, slots=True)
class TableReadInfo:
    delimiter: str | None
    delimiter_name: str
    skiprows: list[int]


def split_preview_line(line: str, delimiter: str | None) -> list[str]:
    if delimiter is None:
        return line.strip().split()
    try:
        return next(csv.reader([line], delimiter=delimiter))
    except csv.Error:
        return line.rstrip("\n\r").split(delimiter)


def detect_delimiter(path: Path, sample: str | None = None) -> tuple[str | None, str]:
    if sample is None:
        sample = path.read_text(encoding="utf-8-sig", errors="replace")[:8192]
    suffix = path.suffix.casefold()
    if suffix == ".csv":
        return ",", "CSV"
    if suffix in {".tsv", ".tab"}:
        return "\t", "TSV"

    lines = [line for line in sample.splitlines() if line.strip()]
    comma_count = sum(line.count(",") for line in lines[:20])
    tab_count = sum(line.count("\t") for line in lines[:20])
    if comma_count > tab_count:
        return ",", "CSV"
    if tab_count > 0:
        return "\t", "TSV"
    return None, "whitespace"


def table_read_info(path: str | Path, min_fields: int = 2) -> TableReadInfo:
    resolved = Path(path)
    sample = resolved.read_text(encoding="utf-8-sig", errors="replace")[:8192]
    delimiter, delimiter_name = detect_delimiter(resolved, sample)
    skiprows: list[int] = []

    with resolved.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
        newline="",
    ) as handle:
        for row_index, line in enumerate(handle):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                skiprows.append(row_index)
                continue

            fields = [field.strip() for field in split_preview_line(line, delimiter)]
            first_field = fields[0].casefold() if fields else ""
            first_key = first_field.split(":", 1)[0].strip().rstrip(":")
            if first_key in ANNOTATION_KEYS or len(fields) < min_fields:
                skiprows.append(row_index)
                continue
            break

    return TableReadInfo(
        delimiter=delimiter,
        delimiter_name=delimiter_name,
        skiprows=skiprows,
    )


def read_table(
    path: str | Path,
    *,
    nrows: int | None = None,
    min_fields: int = 2,
) -> pd.DataFrame:
    info = table_read_info(path, min_fields=min_fields)
    common_kwargs = {
        "header": None,
        "nrows": nrows,
        "dtype": str,
        "keep_default_na": False,
        "skiprows": info.skiprows,
    }
    if info.delimiter_name == "CSV":
        return pd.read_csv(path, **common_kwargs)
    if info.delimiter_name == "TSV":
        return pd.read_csv(path, sep="\t", **common_kwargs)
    return pd.read_csv(path, sep=r"\s+", engine="python", **common_kwargs)


def read_condor_edges(path: str | Path) -> tuple[pd.DataFrame, TableReadInfo]:
    """Read a strict source-target-weight table shared by inspect and execution."""
    resolved = Path(path)
    info = table_read_info(resolved, min_fields=2)
    frame = read_table(resolved, min_fields=2)
    if frame.empty or frame.shape[1] < 2:
        raise ValueError("CONDOR input needs at least source and target columns.")

    first = frame.iloc[0].astype(str).str.casefold().tolist()
    if first[0] in {"source", "from", "regulator", "tf"} and first[1] in {
        "target",
        "to",
        "gene",
    }:
        frame = frame.iloc[1:].reset_index(drop=True)
    if frame.empty:
        raise ValueError("CONDOR input has no data rows.")

    edges = (
        frame.iloc[:, :3].copy() if frame.shape[1] >= 3 else frame.iloc[:, :2].copy()
    )
    if edges.shape[1] == 2:
        edges[2] = "1"
    edges.columns = ["source", "target", "weight"]
    edges["source"] = edges["source"].astype(str).str.strip()
    edges["target"] = edges["target"].astype(str).str.strip()
    invalid_ids = {"", "nan", "none", "null"}
    if (
        edges["source"].str.casefold().isin(invalid_ids).any()
        or edges["target"].str.casefold().isin(invalid_ids).any()
    ):
        raise ValueError("CONDOR source and target IDs must be non-empty.")
    numeric_weight = pd.to_numeric(edges["weight"], errors="coerce")
    if numeric_weight.isna().any():
        bad_rows = numeric_weight.isna()
        ratio = numeric_weight.notna().mean()
        if bad_rows.sum() == 1 and bad_rows.iloc[0]:
            # Every row but the first parses fine, so the likeliest cause is a
            # header row this function did not recognize (it only strips
            # {source,from,regulator,tf}/{target,to,gene} pairs) rather than a
            # bad value in the data itself. Naming that possibility keeps a
            # legitimate rejection from reading as "check your numbers" when
            # the numbers are fine and the header spelling is the problem.
            header_values = list(frame.iloc[0, : edges.shape[1]])
            raise ValueError(
                "CONDOR weight column must be numeric when present; "
                f"numeric ratio is {ratio:.1%}. Only row 1 fails, with "
                f"values {header_values!r} -- if that is a header row, its "
                "column names were not recognized (expected source/target, "
                "optionally with a weight column); rename or remove it. "
                "Otherwise, fix row 1's weight value."
            )
        raise ValueError(
            "CONDOR weight column must be numeric when present; "
            f"numeric ratio is {ratio:.1%}."
        )
    edges["weight"] = numeric_weight
    edges = edges[(edges["source"] != "") & (edges["target"] != "")]
    if edges.empty:
        raise ValueError("CONDOR input has no usable edges.")
    return edges, info
