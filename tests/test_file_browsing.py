"""Browsing what a run produced, and refusing everything else.

Two properties matter here. The window may only see `outputs/`, whatever it
asks for; and a preview must never load the file it is previewing, because
the results this exists to show are hundreds of megabytes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.server import files  # noqa: E402


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """A project with an `outputs/` tree and a secret beside it."""
    root = tmp_path / "project"
    outputs = root / "outputs" / "demo"
    outputs.mkdir(parents=True)
    (root / ".env").write_text("OPENROUTER_API_KEY=sk-secret\n")
    (root / "scripts").mkdir()
    (root / "scripts" / "agent.py").write_text("print('hi')\n")

    (outputs / "net.tsv").write_text(
        "tf\tgene\tweight\n" + "".join(f"TF{i}\tG{i}\t0.{i}\n" for i in range(500))
    )
    (outputs / "report.md").write_text("# PANDA\n\nDone.\n")
    (outputs / "blob.bin").write_bytes(b"\x00\x01\x02")

    monkeypatch.setattr(files, "PROJECT_ROOT", root)
    return root


class TestListing:
    def test_the_root_is_outputs(self, tree):
        assert files.list_directory("").path == "outputs"

    def test_entries_are_project_relative(self, tree):
        entries = files.list_directory("outputs/demo").entries
        assert {entry.path for entry in entries} == {
            "outputs/demo/net.tsv",
            "outputs/demo/report.md",
            "outputs/demo/blob.bin",
        }

    def test_directories_sort_before_files(self, tree):
        (tree / "outputs" / "zzz").mkdir()
        kinds = [entry.kind for entry in files.list_directory("").entries]
        assert kinds == sorted(kinds, key=lambda kind: kind != "directory")

    def test_dotfiles_are_not_listed(self, tree):
        (tree / "outputs" / ".DS_Store").write_text("")
        names = [entry.name for entry in files.list_directory("").entries]
        assert ".DS_Store" not in names


class TestRefusal:
    @pytest.mark.parametrize(
        "requested",
        [
            "../.env",
            "outputs/../.env",
            "outputs/demo/../../../etc/passwd",
            "/etc/passwd",
            "scripts/agent.py",
        ],
    )
    def test_nothing_outside_outputs_can_be_read(self, tree, requested):
        with pytest.raises(files.OutsideRoot):
            files.preview(requested)

    def test_a_symlink_out_of_the_tree_is_not_followed(self, tree):
        link = tree / "outputs" / "escape.md"
        link.symlink_to(tree / ".env")

        with pytest.raises(files.OutsideRoot):
            files.preview("outputs/escape.md")

    def test_a_directory_is_not_a_preview(self, tree):
        with pytest.raises(files.OutsideRoot):
            files.preview("outputs/demo")


class TestPreviews:
    def test_a_table_is_capped_and_says_so(self, tree):
        result = files.preview("outputs/demo/net.tsv")

        assert result.kind == "table"
        assert result.columns == ["tf", "gene", "weight"]
        assert len(result.rows) == files.MAX_ROWS
        assert result.truncated is True
        assert "first" in result.note

    def test_a_short_table_is_not_marked_truncated(self, tree):
        (tree / "outputs" / "small.tsv").write_text("a\tb\n1\t2\n")

        result = files.preview("outputs/small.tsv")

        assert result.rows == [["1", "2"]]
        assert result.truncated is False
        assert result.note == ""

    def test_markdown_comes_back_as_text(self, tree):
        result = files.preview("outputs/demo/report.md")

        assert result.kind == "text"
        assert result.text.startswith("# PANDA")

    def test_an_unknown_type_says_it_has_no_viewer(self, tree):
        result = files.preview("outputs/demo/blob.bin")

        assert result.kind == "binary"
        assert "no viewer" in result.note
        assert result.text == ""


def test_an_archive_is_described_without_loading_its_arrays(tree):
    numpy = pytest.importorskip("numpy")
    numpy.savez(
        tree / "outputs" / "components.npz",
        psi=numpy.zeros((2, 4)),
        q=numpy.ones((5, 4)),
    )

    result = files.preview("outputs/components.npz")

    assert result.kind == "arrays"
    assert {entry["name"] for entry in result.arrays} == {"psi", "q"}
    assert [entry["shape"] for entry in result.arrays if entry["name"] == "q"] == [
        [5, 4]
    ]
    # Nothing in the preview carries array values.
    assert result.rows == [] and result.text == ""


class TestHeaderAlignment:
    """Some NetZoo outputs write a space-separated header above tab rows."""

    def test_a_header_that_matches_the_data_width_is_re_split(self, tree):
        (tree / "outputs" / "mixed.tsv").write_text(
            "regulator gene weight\nTF1\tGeneA\t0.5\n"
        )

        result = files.preview("outputs/mixed.tsv")

        assert result.columns == ["regulator", "gene", "weight"]
        assert result.rows == [["TF1", "GeneA", "0.5"]]

    def test_a_header_that_does_not_match_is_left_alone(self, tree):
        """Guessing here would turn a real one-column table into nonsense."""
        (tree / "outputs" / "prose.tsv").write_text(
            "a description with spaces\tsecond\nx\ty\n"
        )

        result = files.preview("outputs/prose.tsv")

        assert result.columns == ["a description with spaces", "second"]

    def test_a_single_column_table_keeps_its_one_column(self, tree):
        (tree / "outputs" / "one.tsv").write_text("gene symbol\nAHR\nAR\n")

        result = files.preview("outputs/one.tsv")

        assert result.columns == ["gene symbol"]


class TestBufferedPreviews:
    def test_table_pages_reconstruct_every_row_without_repeating_the_header(self, tree):
        first = files.preview("outputs/demo/net.tsv")
        rows = list(first.rows)
        current = first
        while current.next_offset is not None:
            current = files.preview("outputs/demo/net.tsv", offset=current.next_offset, version=first.version)
            assert current.columns == first.columns
            rows.extend(current.rows)
        assert len(rows) == 500
        assert [row[0] for row in rows] == [f"TF{i}" for i in range(500)]

    def test_csv_pages_keep_quoted_newlines_intact(self, tree, monkeypatch):
        monkeypatch.setattr(files, "MAX_ROWS", 1)
        (tree / "outputs" / "quoted.csv").write_text('name,note\r\nA,"line 1\nline 2"\r\nB,last\r\n')
        first = files.preview("outputs/quoted.csv")
        second = files.preview("outputs/quoted.csv", offset=first.next_offset, version=first.version)
        assert first.rows == [["A", "line 1\nline 2"]]
        assert second.rows == [["B", "last"]]
        assert second.next_offset is None

    def test_text_pages_do_not_split_utf8_characters(self, tree, monkeypatch):
        monkeypatch.setattr(files, "MAX_TEXT", 7)
        text = "文字🙂test\n" * 10
        (tree / "outputs" / "unicode.log").write_text(text)
        current = files.preview("outputs/unicode.log")
        parts = [current.text]
        while current.next_offset is not None:
            current = files.preview("outputs/unicode.log", offset=current.next_offset, version=current.version)
            parts.append(current.text)
        assert "".join(parts) == text

    def test_changed_files_must_restart_the_preview(self, tree):
        first = files.preview("outputs/demo/net.tsv")
        with (tree / "outputs" / "demo" / "net.tsv").open("a") as handle:
            handle.write("new\trow\t1\n")
        with pytest.raises(files.FileChanged, match="changed"):
            files.preview(first.path, offset=first.next_offset, version=first.version)

    def test_wide_tables_cap_columns_and_disclose_the_actual_width(self, tree):
        values = [str(index) for index in range(100)]
        (tree / "outputs" / "wide.tsv").write_text("\t".join(values) + "\n" + "\t".join(values) + "\n")
        result = files.preview("outputs/wide.tsv")
        assert len(result.columns) == len(result.rows[0]) == files.MAX_COLUMNS
        assert result.total_columns == 100
        assert result.truncated and result.next_offset is None
        assert "columns" in result.note

    def test_oversized_records_are_refused_with_a_useful_message(self, tree, monkeypatch):
        monkeypatch.setattr(files, "MAX_RECORD_BYTES", 20)
        (tree / "outputs" / "huge.tsv").write_text("header\n" + "x" * 30)
        with pytest.raises(files.PreviewInvalid, match="dedicated data viewer"):
            files.preview("outputs/huge.tsv")

    def test_multiline_records_are_also_bounded(self, tree, monkeypatch):
        monkeypatch.setattr(files, "MAX_RECORD_BYTES", 20)
        (tree / "outputs" / "huge.csv").write_text('name,note\nA,"' + "line\n" * 20 + 'end"\n')
        with pytest.raises(files.PreviewInvalid):
            files.preview("outputs/huge.csv")

    def test_directory_pages_are_stable_and_hide_external_symlinks(self, tree):
        directory = tree / "outputs" / "many"
        directory.mkdir()
        for index in range(250):
            (directory / f"file-{index:03}.log").write_text("ok")
        (directory / "secret.log").symlink_to(tree / ".env")
        pages = [files.list_directory("outputs/many", offset=offset) for offset in (0, 100, 200)]
        assert [page.has_more for page in pages] == [True, True, False]
        assert all(page.total == 250 for page in pages)
        assert len({entry.path for page in pages for entry in page.entries}) == 250

    def test_a_project_with_no_outputs_starts_with_an_empty_listing(self, tree):
        import shutil
        shutil.rmtree(tree / "outputs")
        result = files.list_directory()
        assert result.path == "outputs" and result.total == 0
