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
