from __future__ import annotations

import os
import sys
import time
from dataclasses import replace
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from workflow_registry import ACTION_DEFINITIONS, DiscoverySpec  # noqa: E402

from netzoo_agent_core.data.resource_inventory import (  # noqa: E402
    InventoryLimits,
    inventory_workspace_resources,
)


def _definitions(action, *, roles, hints, validators=("always_valid",)):
    definitions = dict(ACTION_DEFINITIONS)
    definitions[action] = replace(
        ACTION_DEFINITIONS[action],
        discovery=DiscoverySpec(
            input_roles=roles,
            filename_hints=hints,
            validator_ids=validators,
        ),
    )
    return definitions


def test_inventory_uses_only_synthetic_registry_data(tmp_path):
    study = tmp_path / "study-a"
    study.mkdir()
    (study / "alpha.tsv").write_text("id\ts1\nsignal\t1\n", encoding="utf-8")
    (study / "beta.tsv").write_text(
        "source\ttarget\na\tb\n", encoding="utf-8"
    )
    definitions = dict(ACTION_DEFINITIONS)
    definitions["format_expression"] = replace(
        ACTION_DEFINITIONS["format_expression"],
        discovery=DiscoverySpec(
            input_roles=("primary", "relation"),
            filename_hints={"primary": ("alpha",), "relation": ("beta",)},
            validator_ids=("always_valid",),
        ),
    )

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=definitions,
        validators={"always_valid": lambda values, spec: (True, "validated")},
    )

    assert result.validated_bundles[0].directory == "study-a"
    assert result.validated_bundles[0].inputs == {
        "primary": "study-a/alpha.tsv",
        "relation": "study-a/beta.tsv",
    }


def test_inventory_reports_partial_candidates_with_missing_roles(tmp_path):
    study = tmp_path / "study"
    study.mkdir()
    (study / "alpha.tsv").write_text("data\n", encoding="utf-8")

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary", "relation"),
            hints={"primary": ("alpha",), "relation": ("beta",)},
        ),
        validators={"always_valid": lambda values, spec: (True, "validated")},
    )

    assert result.validated_bundles == []
    assert result.partial_candidates[0].matched_inputs == {
        "primary": "study/alpha.tsv"
    }
    assert result.partial_candidates[0].missing_inputs == ["relation"]


def test_inventory_orders_complete_and_partial_results_deterministically(tmp_path):
    for directory_name in ("z-complete", "a-partial", "a-complete"):
        directory = tmp_path / directory_name
        directory.mkdir()
        (directory / "alpha.tsv").write_text("data\n", encoding="utf-8")
        if directory_name.endswith("complete"):
            (directory / "beta.tsv").write_text("data\n", encoding="utf-8")

    kwargs = {
        "definitions": _definitions(
            "format_expression",
            roles=("primary", "relation"),
            hints={"primary": ("alpha",), "relation": ("beta",)},
        ),
        "validators": {
            "always_valid": lambda values, spec: (True, "validated")
        },
    }
    first = inventory_workspace_resources(
        tmp_path, ["format_expression"], **kwargs
    )
    second = inventory_workspace_resources(
        tmp_path, ["format_expression"], **kwargs
    )

    assert [bundle.directory for bundle in first.validated_bundles] == [
        "a-complete",
        "z-complete",
    ]
    assert [item.directory for item in first.partial_candidates] == ["a-partial"]
    assert first.model_dump() == second.model_dump()


def test_inventory_aggregates_a_bundle_across_compatible_actions(tmp_path):
    study = tmp_path / "study"
    study.mkdir()
    (study / "alpha.tsv").write_text("data\n", encoding="utf-8")
    definitions = _definitions(
        "format_expression",
        roles=("primary",),
        hints={"primary": ("alpha",)},
    )
    definitions["convert_expression"] = replace(
        ACTION_DEFINITIONS["convert_expression"],
        discovery=definitions["format_expression"].discovery,
    )

    result = inventory_workspace_resources(
        tmp_path,
        ["convert_expression", "format_expression"],
        definitions=definitions,
        validators={"always_valid": lambda values, spec: (True, "validated")},
    )

    assert len(result.validated_bundles) == 1
    assert result.validated_bundles[0].compatible_actions == [
        "convert_expression",
        "format_expression",
    ]


def test_returned_path_limit_counts_an_aggregated_path_once(tmp_path):
    (tmp_path / "alpha.tsv").write_text("data\n", encoding="utf-8")
    definitions = _definitions(
        "format_expression",
        roles=("primary",),
        hints={"primary": ("alpha",)},
    )
    definitions["convert_expression"] = replace(
        ACTION_DEFINITIONS["convert_expression"],
        discovery=definitions["format_expression"].discovery,
    )

    result = inventory_workspace_resources(
        tmp_path,
        ["convert_expression", "format_expression"],
        definitions=definitions,
        validators={"always_valid": lambda values, spec: (True, "validated")},
        limits=InventoryLimits(max_returned_paths=1),
    )

    assert result.validated_bundles[0].compatible_actions == [
        "convert_expression",
        "format_expression",
    ]
    assert result.truncated is False


def test_inventory_records_unreadable_files_without_failing_the_scan(
    tmp_path, monkeypatch
):
    study = tmp_path / "study"
    study.mkdir()
    unreadable = study / "alpha.tsv"
    unreadable.write_text("data\n", encoding="utf-8")
    (study / "beta.tsv").write_text("data\n", encoding="utf-8")
    original_open = os.open

    def guarded_open(path, flags, mode=0o777, *, dir_fd=None):
        if path == unreadable.name and dir_fd is not None:
            raise PermissionError("denied")
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", guarded_open)

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary", "relation"),
            hints={"primary": ("alpha",), "relation": ("beta",)},
        ),
        validators={"always_valid": lambda values, spec: (True, "validated")},
    )

    assert result.rejected_summary == {"unreadable": 1}
    assert result.partial_candidates[0].missing_inputs == ["primary"]


def test_inventory_stops_at_the_visited_file_limit(tmp_path):
    (tmp_path / "alpha.tsv").write_text("data\n", encoding="utf-8")
    (tmp_path / "beta.tsv").write_text("data\n", encoding="utf-8")

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary",),
            hints={"primary": ("alpha",)},
        ),
        validators={"always_valid": lambda values, spec: (True, "validated")},
        limits=InventoryLimits(max_visited_files=1),
    )

    assert result.visited_file_count == 1
    assert result.truncated is True


def test_inventory_excludes_symlink_files_and_directories(tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    target = outside / "alpha.tsv"
    target.write_text("data\n", encoding="utf-8")
    (tmp_path / "linked-alpha.tsv").symlink_to(target)
    (tmp_path / "linked-directory").symlink_to(outside, target_is_directory=True)
    validator_calls = []

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary",),
            hints={"primary": ("alpha",)},
        ),
        validators={
            "always_valid": lambda values, spec: (
                validator_calls.append(values) is None,
                "validated",
            )
        },
    )

    assert result.validated_bundles == []
    assert result.rejected_summary == {"symlink": 1}
    assert validator_calls == []


def test_inventory_rejects_an_explicit_path_through_a_symlinked_parent(tmp_path):
    real_directory = tmp_path / "real"
    real_directory.mkdir()
    (real_directory / "alpha.tsv").write_text("data\n", encoding="utf-8")
    (tmp_path / "linked").symlink_to(real_directory, target_is_directory=True)

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary",),
            hints={"primary": ("alpha",)},
        ),
        validators={"always_valid": lambda values, spec: (True, "validated")},
        explicit_inputs={"primary": "linked/alpha.tsv"},
    )

    assert result.validated_bundles == []
    assert result.rejected_summary == {"symlink": 1}


def test_inventory_rejects_an_explicit_path_resolved_outside_root(tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}-outside.tsv"
    outside.write_text("data\n", encoding="utf-8")

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary",),
            hints={"primary": ("alpha",)},
        ),
        validators={"always_valid": lambda values, spec: (True, "validated")},
        explicit_inputs={"primary": str(outside)},
    )

    assert result.validated_bundles == []
    assert result.rejected_summary == {"outside_root": 1}


def test_inventory_stops_descent_at_the_depth_limit(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "alpha.tsv").write_text("data\n", encoding="utf-8")

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary",),
            hints={"primary": ("alpha",)},
        ),
        validators={"always_valid": lambda values, spec: (True, "validated")},
        limits=InventoryLimits(max_depth=0),
    )

    assert result.visited_file_count == 0
    assert result.validated_bundles == []
    assert result.truncated is True


def test_inventory_stops_at_the_candidate_group_limit(tmp_path):
    for name in ("first", "second"):
        directory = tmp_path / name
        directory.mkdir()
        (directory / "alpha.tsv").write_text("data\n", encoding="utf-8")

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary",),
            hints={"primary": ("alpha",)},
        ),
        validators={"always_valid": lambda values, spec: (True, "validated")},
        limits=InventoryLimits(max_candidate_groups=1),
    )

    assert [bundle.directory for bundle in result.validated_bundles] == ["first"]
    assert result.truncated is True


def test_inventory_stops_before_exceeding_the_returned_path_limit(tmp_path):
    (tmp_path / "alpha.tsv").write_text("data\n", encoding="utf-8")
    (tmp_path / "beta.tsv").write_text("data\n", encoding="utf-8")

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary", "relation"),
            hints={"primary": ("alpha",), "relation": ("beta",)},
        ),
        validators={"always_valid": lambda values, spec: (True, "validated")},
        limits=InventoryLimits(max_returned_paths=1),
    )

    assert result.validated_bundles == []
    assert result.partial_candidates == []
    assert result.truncated is True


def test_inventory_never_opens_a_file_over_the_byte_limit(tmp_path, monkeypatch):
    oversized = tmp_path / "alpha.tsv"
    oversized.write_text("too large\n", encoding="utf-8")
    original_open = Path.open

    def guarded_open(path, *args, **kwargs):
        if path == oversized:
            raise AssertionError("oversized file was opened")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary",),
            hints={"primary": ("alpha",)},
        ),
        validators={"always_valid": lambda values, spec: (True, "validated")},
        limits=InventoryLimits(max_file_bytes=1),
    )

    assert result.rejected_summary == {"too_large": 1}
    assert result.truncated is True


def test_inventory_never_opens_a_non_regular_file(tmp_path, monkeypatch):
    fifo = tmp_path / "alpha.tsv"
    os.mkfifo(fifo)
    original_open = Path.open

    def guarded_open(path, *args, **kwargs):
        if path == fifo:
            raise AssertionError("non-regular file was opened")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary",),
            hints={"primary": ("alpha",)},
        ),
        validators={"always_valid": lambda values, spec: (True, "validated")},
    )

    assert result.validated_bundles == []
    assert result.rejected_summary == {"not_regular_file": 1}


def test_inventory_stops_at_the_duration_limit(tmp_path, monkeypatch):
    (tmp_path / "alpha.tsv").write_text("data\n", encoding="utf-8")
    timestamps = iter((0.0, 0.0, 6.0))
    monkeypatch.setattr(
        "netzoo_agent_core.data.resource_inventory.time.monotonic",
        lambda: next(timestamps),
    )

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary",),
            hints={"primary": ("alpha",)},
        ),
        validators={"always_valid": lambda values, spec: (True, "validated")},
        limits=InventoryLimits(max_duration_seconds=5.0),
    )

    assert result.visited_file_count == 0
    assert result.truncated is True


def test_duration_limit_is_rechecked_before_candidate_validation(
    tmp_path, monkeypatch
):
    (tmp_path / "alpha.tsv").write_text("data\n", encoding="utf-8")
    timestamps = iter((0.0, 0.0, 0.0, 6.0))
    monkeypatch.setattr(
        "netzoo_agent_core.data.resource_inventory.time.monotonic",
        lambda: next(timestamps),
    )
    validator_calls = []

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary",),
            hints={"primary": ("alpha",)},
        ),
        validators={
            "always_valid": lambda values, spec: (
                validator_calls.append(values) is None,
                "validated",
            )
        },
        limits=InventoryLimits(max_duration_seconds=5.0),
    )

    assert result.truncated is True
    assert result.validated_bundles == []
    assert validator_calls == []


def test_inventory_discards_a_candidate_when_validation_exceeds_duration(
    tmp_path,
):
    (tmp_path / "alpha.tsv").write_text("data\n", encoding="utf-8")
    worker_pid = tmp_path / "validator.pid"

    def slow_validator(values, spec):
        worker_pid.write_text(str(os.getpid()), encoding="utf-8")
        time.sleep(0.5)
        return True, "validated"

    started = time.monotonic()
    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary",),
            hints={"primary": ("alpha",)},
        ),
        validators={"always_valid": slow_validator},
        limits=InventoryLimits(max_duration_seconds=0.05),
    )
    elapsed = time.monotonic() - started

    assert elapsed < 0.35
    assert result.truncated is True
    assert result.validated_bundles == []
    pid = int(worker_pid.read_text(encoding="utf-8"))
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def test_validator_reads_a_bounded_snapshot_after_workspace_source_replacement(
    tmp_path,
):
    source = tmp_path / "alpha.tsv"
    source.write_bytes(b"safe\n")
    outside = tmp_path.parent / f"{tmp_path.name}-outside.tsv"
    outside.write_bytes(b"x" * 64)

    def replacing_validator(values, spec):
        source.unlink()
        source.symlink_to(outside)
        observed = Path(values["primary"]).read_bytes()
        return observed == b"safe\n", "bounded_snapshot"

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary",),
            hints={"primary": ("alpha",)},
        ),
        validators={"always_valid": replacing_validator},
        limits=InventoryLimits(max_file_bytes=8),
    )

    assert result.validated_bundles[0].validation_reasons == ["bounded_snapshot"]
    assert source.is_symlink()


def test_descriptor_open_fails_closed_when_candidate_is_swapped_to_symlink(
    tmp_path, monkeypatch
):
    source = tmp_path / "alpha.tsv"
    source.write_bytes(b"safe\n")
    outside = tmp_path.parent / f"{tmp_path.name}-outside.tsv"
    outside.write_bytes(b"outside\n")
    original_open = os.open
    swapped = False

    def racing_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if path == "alpha.tsv" and dir_fd is not None and not swapped:
            swapped = True
            source.unlink()
            source.symlink_to(outside)
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", racing_open)

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary",),
            hints={"primary": ("alpha",)},
        ),
        validators={"always_valid": lambda values, spec: (True, "validated")},
    )

    assert result.validated_bundles == []
    assert result.rejected_summary["symlink"] == 1


def test_inventory_never_opens_an_explicit_disallowed_extension(
    tmp_path, monkeypatch
):
    disallowed = tmp_path / "alpha.json"
    disallowed.write_text("{}\n", encoding="utf-8")
    original_open = Path.open

    def guarded_open(path, *args, **kwargs):
        if path == disallowed:
            raise AssertionError("disallowed extension was opened")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary",),
            hints={"primary": ("alpha",)},
        ),
        validators={"always_valid": lambda values, spec: (True, "validated")},
        explicit_inputs={"primary": "alpha.json"},
    )

    assert result.validated_bundles == []
    assert result.rejected_summary == {"disallowed_extension": 1}


def test_inventory_contains_validator_failures_to_one_candidate(tmp_path):
    (tmp_path / "alpha.tsv").write_text("data\n", encoding="utf-8")

    def broken_validator(values, spec):
        assert Path(values["primary"]).is_absolute()
        raise RuntimeError("parser crashed")

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=_definitions(
            "format_expression",
            roles=("primary",),
            hints={"primary": ("alpha",)},
        ),
        validators={"always_valid": broken_validator},
    )

    assert result.validated_bundles == []
    assert result.rejected_summary == {"validation_error": 1}
    assert result.errors == ["validation failed: RuntimeError"]
