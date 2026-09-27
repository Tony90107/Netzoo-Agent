"""Read-only diagnostics shared by /doctor and the desktop environment view.

This process cannot inspect the host Docker socket. Host image checks belong
to the desktop shell, and module presence is never presented as execution
approval or a substitute for the input and Plan Evaluator gates.
"""
from __future__ import annotations

from datetime import datetime, timezone
from importlib import metadata
import os
from pathlib import Path
import platform

from . import settings

METHODS = (
    "PANDA", "PUMA", "LIONESS", "CONDOR", "COBRA", "SAMBAR",
    "DRAGON", "OTTER", "GIRAFFE", "BONOBO",
)


def environment_report() -> dict:
    checks: list[dict[str, str]] = []

    def add(key: str, label: str, status: str, detail: str, remedy: str = ""):
        checks.append(dict(key=key, label=label, status=status, detail=detail, remedy=remedy))

    container = Path("/.dockerenv").is_file()
    add("container", "Docker container", "passed" if container else "warning",
        "This process is running in Docker." if container else "This process is running outside Docker.",
        "Launch the desktop app or start docker compose up -d netzoo-daemon." if not container else "")
    add("python", "Python", "passed", platform.python_version())
    try:
        distribution = metadata.distribution("netZooPy")
        version = distribution.version
        source = Path(os.environ.get("NETZOOPY_SRC") or distribution.locate_file("netZooPy"))
        package_root = source / "netZooPy" if (source / "netZooPy").is_dir() else source
        add("package", "netZooPy package", "passed", f"{version} · {source}")
    except metadata.PackageNotFoundError:
        version = "not installed"
        package_root = Path(os.environ.get("NETZOOPY_SRC") or "/opt/netZooPy") / "netZooPy"
        add("package", "netZooPy package", "failed", "netZooPy is not installed in this process.",
            "Build the project image with docker compose build netzoo, then restart the desktop app.")
    available = [name for name in METHODS if (package_root / name.lower()).is_dir()
                 or (package_root / f"{name.lower()}.py").is_file()]
    missing = [name for name in METHODS if name not in available]
    add("modules", "Algorithm source modules", "warning" if missing else "passed",
        f"Found: {', '.join(available) or 'none'}." + (f" Missing: {', '.join(missing)}." if missing else ""),
        "Rebuild the pinned project image to restore missing modules." if missing else "")
    add("api_key", "Agent API key", "passed" if os.environ.get("OPENROUTER_API_KEY", "").strip() else "warning",
        "Configured (value hidden)." if os.environ.get("OPENROUTER_API_KEY", "").strip() else "Not configured.",
        "Set OPENROUTER_API_KEY in the project's .env and restart the desktop app." if not os.environ.get("OPENROUTER_API_KEY", "").strip() else "")
    outputs = settings.PROJECT_ROOT / "outputs"
    writable = outputs if outputs.exists() else outputs.parent
    ready = (outputs.is_dir() or not outputs.exists()) and os.access(writable, os.W_OK)
    add("outputs", "Output directory", "passed" if ready else "failed", str(outputs),
        "Ensure outputs/ is a directory and the mounted project is writable." if not ready else "")
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "netzoopy_version": version,
        "source_ref": os.environ.get("NETZOOPY_REF", "").strip(),
        "available_methods": available,
        "note": "Module presence checks source files only. Each analysis still validates inputs and its Work Plan before execution. Host Docker and image checks are available in the desktop Environment view.",
    }


def render_environment_report() -> str:
    report = environment_report()
    lines = ["### Environment check", "| Check | Status | Detail |", "| --- | --- | --- |"]
    for check in report["checks"]:
        detail = check["detail"].replace("|", "\\|")
        lines.append(f"| {check['label']} | {check['status']} | {detail} |")
    for check in report["checks"]:
        if check["remedy"]:
            lines.append(f"\n**{check['label']} repair:** {check['remedy']}")
    if report["source_ref"]:
        lines.append(f"\nSource commit: `{report['source_ref']}`")
    lines.append(f"\n{report['note']}")
    return "\n".join(lines)
