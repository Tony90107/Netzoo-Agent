"""Translating between the paths a person sees and the paths the agent uses.

The agent runs in a container where the project is ``/work``; the window runs
on the host where the same project is somewhere under the user's home. A file
picked in Finder is a host path the agent cannot open, and a path in a plan is
a container path the user cannot find.

This is only a translation. It is not a permission check and it does not
replace one: ``data.paths`` and the workflow preflight still decide what the
agent may read and write, and they run on the container path exactly as they
did before. What this adds is a refusal to translate anything outside the
project at all, so a host path from a file dialog cannot name
``/etc/passwd`` and arrive as something the rest of the system will consider.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import PurePosixPath

from ..settings import PROJECT_ROOT

__all__ = ["PathMapper", "PathOutsideProject"]


class PathOutsideProject(ValueError):
    """A path that does not name something inside the project."""


@dataclass(frozen=True, slots=True)
class PathMapper:
    """Map ``<host project>/x`` to ``<container project>/x`` and back.

    ``host_root`` comes from the desktop shell, which is the only part of the
    system that knows where the project lives on the host. Without it the
    mapper still validates container paths; it just cannot translate, which
    is the right behaviour for a daemon started by hand.
    """

    container_root: PurePosixPath = PurePosixPath(str(PROJECT_ROOT))
    host_root: PurePosixPath | None = None

    @classmethod
    def from_environment(cls) -> "PathMapper":
        configured = os.environ.get("NETZOO_HOST_PROJECT_ROOT", "").strip()
        return cls(
            container_root=PurePosixPath(str(PROJECT_ROOT)),
            host_root=PurePosixPath(configured) if configured else None,
        )

    @property
    def can_translate(self) -> bool:
        return self.host_root is not None

    def _within(self, path: PurePosixPath, root: PurePosixPath) -> PurePosixPath:
        # Normalise `..` textually; these are foreign paths that may not exist
        # on this side of the boundary, so they cannot be resolved on disk.
        parts: list[str] = []
        for part in path.parts:
            if part == "..":
                if not parts:
                    raise PathOutsideProject(f"{path} escapes the project")
                parts.pop()
            elif part not in (".",):
                parts.append(part)
        normalised = PurePosixPath(*parts)
        if not normalised.is_relative_to(root):
            raise PathOutsideProject(f"{path} is outside {root}")
        return normalised.relative_to(root)

    def to_container(self, host_path: str) -> str:
        """A path as the user sees it becomes one the agent can open."""
        if self.host_root is None:
            raise PathOutsideProject(
                "the desktop shell did not say where the project lives on the host"
            )
        candidate = PurePosixPath(host_path)
        if not candidate.is_absolute():
            # A relative path is already project-relative in both worlds.
            return str(self.container_root / candidate)
        return str(self.container_root / self._within(candidate, self.host_root))

    def to_host(self, container_path: str) -> str:
        """A path in a plan becomes one the user can find in Finder.

        Returns the container path unchanged when the shell did not supply a
        host root, because a wrong host path would be worse than an honest
        container one.
        """
        candidate = PurePosixPath(container_path)
        if not candidate.is_absolute():
            candidate = self.container_root / candidate
        relative = self._within(candidate, self.container_root)
        if self.host_root is None:
            return str(self.container_root / relative)
        return str(self.host_root / relative)

    def relative(self, container_path: str) -> str:
        """The project-relative path, which is what both sides agree on."""
        candidate = PurePosixPath(container_path)
        if not candidate.is_absolute():
            candidate = self.container_root / candidate
        return str(self._within(candidate, self.container_root))
