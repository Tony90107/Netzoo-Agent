"""Path tokens in a request are locations, not workflow names (Log 191).

`data/bonobo-toy/expression.tsv` names a folder somebody called bonobo-toy; it
does not name BONOBO. Log 137 found blind prompts answered "correctly" only
because the path said so, and every blind test since has had to copy its data
to neutral folders first. Each check that asks "did the requester write this
workflow's name" therefore reads the request with its path tokens blanked out.
Readers that look *for* files (input availability, named folders) keep the
full text.

A token counts as a path when it contains a separator and ends with one, starts
at a root (`/`, `./`, `../`, `~`), has a file extension on its last segment, or
exists under the project root; or, without a separator, when it ends with a
data-file extension. `PANDA/PUMA` or `TF/gene` is none of these and still reads
as words.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..settings import PROJECT_ROOT

__all__ = ["is_path_token", "without_path_tokens"]

_CHUNK = re.compile(r"[^\s\"'`()\[\]{}<>，。；：、「」（）]+")
_EXTENSION = re.compile(r"\.[A-Za-z][A-Za-z0-9]{0,7}$")
_DATA_FILE = re.compile(
    r"\.(?:tsv|csv|txt|gmt|npy|npz|h5|hdf5|h5ad|json|ya?ml|parquet|feather|xlsx?"
    r"|rds|rda|pkl|pickle|dat|mtx|gz|bz2|zip|tar)$",
    re.IGNORECASE,
)


def _exists(root: Path, token: str) -> bool:
    try:
        return (root / token).exists()
    except (OSError, ValueError):
        return False


def is_path_token(token: str, root: Path = PROJECT_ROOT) -> bool:
    token = token.rstrip(".,;:!?")
    if not token:
        return False
    if "/" not in token and "\\" not in token:
        return bool(_DATA_FILE.search(token))
    last = re.split(r"[\\/]", token.rstrip("/\\"))[-1]
    return (
        token.endswith(("/", "\\"))
        or token.startswith(("/", "./", "../", "~"))
        or bool(_EXTENSION.search(last))
        or _exists(root, token)
    )


def without_path_tokens(text: str, root: Path = PROJECT_ROOT) -> str:
    """The text with every path token replaced by a space."""
    return _CHUNK.sub(
        lambda found: " " if is_path_token(found.group(), root) else found.group(),
        text,
    )


_TENX_MATRIX = ("matrix.mtx", "matrix.mtx.gz")


def tenx_directories(text: str, root: Path = PROJECT_ROOT) -> list[str]:
    """The path tokens in `text` that name a 10x Matrix Market directory (one holding matrix.mtx[.gz]).

    Such a directory has no extension, so prose ("counts in data/run/counts_10x") binds it by what it holds, never
    by its name (2026-11-10: unbound, the request's cell metadata table was read as the single-cell matrix).
    """
    found: list[str] = []
    for chunk in _CHUNK.findall(text):
        token = chunk.rstrip(".,;:!?")
        if "/" not in token and "\\" not in token:
            continue
        try:
            directory = Path(token).expanduser()
            directory = directory if directory.is_absolute() else root / token
            if directory.is_dir() and any((directory / name).is_file() for name in _TENX_MATRIX):
                found.append(token)
        except (OSError, ValueError):
            continue
    return list(dict.fromkeys(found))


_OUTPUT_DIRECTORY = re.compile(
    r"\b(?:write|save|store|output|put)\b[^/~.\n]{0,40}?\b(?:to|in|into|at|under)\s+(\S+)", re.IGNORECASE)


def output_directory(text: str) -> str | None:
    """The folder a request says to write to ("output to tmp/run", "save the results to /data/out/").

    A path whose last part has an extension names a file, not a folder, and is left to the file roles. Before
    2026-11-10 "output to <folder>" was not read: PORCUPINE asked for it again and SPONGE silently wrote elsewhere.
    """
    for found in _OUTPUT_DIRECTORY.finditer(text):
        token = found.group(1).rstrip(".,;:!?)")
        last = re.split(r"[\\/]", token.rstrip("/\\"))[-1]
        if ("/" in token or "\\" in token or token.startswith(("~", "."))) and not _EXTENSION.search(last):
            return token
    return None
