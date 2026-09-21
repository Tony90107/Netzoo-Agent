"""The host/container translation, and what it refuses.

This is the boundary a file dialog crosses. It is not the permission check —
`data.paths` and the workflow preflight still decide what may be read and
written — but it is what stops a host path naming something outside the
project and arriving as a container path the rest of the system will
consider.
"""

from __future__ import annotations

import sys
from pathlib import Path, PurePosixPath

import pytest

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.server.path_mapper import (  # noqa: E402
    PathMapper,
    PathOutsideProject,
)

HOST = "/Users/someone/Documents/LLM AGENT/netzoo_agent"
CONTAINER = "/work"


def mapper(host: str | None = HOST) -> PathMapper:
    return PathMapper(
        container_root=PurePosixPath(CONTAINER),
        host_root=PurePosixPath(host) if host else None,
    )


class TestTranslation:
    def test_a_picked_file_becomes_a_path_the_agent_can_open(self):
        assert (
            mapper().to_container(f"{HOST}/data/official-toy/ToyExpressionData.txt")
            == "/work/data/official-toy/ToyExpressionData.txt"
        )

    def test_a_path_in_a_plan_becomes_one_the_user_can_find(self):
        assert (
            mapper().to_host("/work/outputs/demo/ToyExpressionData-panda.tsv")
            == f"{HOST}/outputs/demo/ToyExpressionData-panda.tsv"
        )

    def test_the_round_trip_is_stable(self):
        original = f"{HOST}/outputs/demo/x.tsv"
        assert mapper().to_host(mapper().to_container(original)) == original

    def test_the_project_root_itself_maps(self):
        assert mapper().to_container(HOST) == "/work"
        assert mapper().to_host("/work") == HOST

    def test_a_relative_path_means_the_same_thing_on_both_sides(self):
        assert mapper().to_container("data/toy.tsv") == "/work/data/toy.tsv"
        assert mapper().relative("/work/data/toy.tsv") == "data/toy.tsv"


class TestRefusal:
    @pytest.mark.parametrize(
        "host_path",
        [
            "/etc/passwd",
            "/Users/someone/Documents/other-project/secrets.env",
            "/Users/someone/.ssh/id_rsa",
            "/",
        ],
    )
    def test_a_path_outside_the_project_is_refused(self, host_path):
        with pytest.raises(PathOutsideProject):
            mapper().to_container(host_path)

    def test_a_traversal_that_escapes_is_refused(self):
        with pytest.raises(PathOutsideProject):
            mapper().to_container(f"{HOST}/data/../../secrets")

    def test_a_traversal_that_stays_inside_is_allowed(self):
        assert (
            mapper().to_container(f"{HOST}/data/../outputs/x.tsv")
            == "/work/outputs/x.tsv"
        )

    def test_a_container_path_outside_the_project_is_refused(self):
        with pytest.raises(PathOutsideProject):
            mapper().to_host("/etc/passwd")

    def test_a_sibling_directory_with_a_shared_prefix_is_not_inside(self):
        """`/work-scratch` starts with `/work` but is a different directory."""
        with pytest.raises(PathOutsideProject):
            mapper().to_host("/work-scratch/x")


class TestWithoutAShell:
    """A daemon started by hand has no host root; it must stay honest."""

    def test_translation_to_container_is_refused_rather_than_guessed(self):
        with pytest.raises(PathOutsideProject):
            mapper(host=None).to_container("/anywhere/x.tsv")

    def test_a_container_path_is_shown_as_itself(self):
        assert mapper(host=None).to_host("/work/outputs/x.tsv") == "/work/outputs/x.tsv"

    def test_it_says_it_cannot_translate(self):
        assert mapper(host=None).can_translate is False
        assert mapper().can_translate is True
