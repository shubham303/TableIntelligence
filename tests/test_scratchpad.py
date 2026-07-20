"""Tests for the per-session plain-text scratchpad.

_DIR is redirected into tmp_path so tests never touch the real ~/.tableintelligence.
"""
import pytest

from tabint import scratchpad


@pytest.fixture(autouse=True)
def isolate_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(scratchpad, "_DIR", tmp_path / ".tableintelligence")


def test_add_read_roundtrip():
    scratchpad.add("s_1", "first note")
    scratchpad.add("s_1", "second note")
    text = scratchpad.read("s_1")
    assert "first note" in text
    assert "second note" in text
    # Each chunk carries a date-time header.
    assert text.count("## ") == 2


def test_read_empty_when_nothing_written():
    assert scratchpad.read("s_never") == ""
    assert scratchpad.search("s_never", "x") == []


def test_search_is_case_insensitive_substring():
    scratchpad.add("s_2", "dept explains 12% of SALARY variance")
    scratchpad.add("s_2", "log transform did not help clustering")
    assert len(scratchpad.search("s_2", "salary")) == 1
    assert len(scratchpad.search("s_2", "CLUSTER")) == 1
    assert scratchpad.search("s_2", "nonexistent") == []


def test_search_returns_whole_chunk_with_timestamp():
    scratchpad.add("s_3", "keep this finding")
    (match,) = scratchpad.search("s_3", "finding")
    assert match.startswith("## ")
    assert "keep this finding" in match


def test_sessions_are_separate_files():
    scratchpad.add("s_a", "belongs to A")
    scratchpad.add("s_b", "belongs to B")
    assert "belongs to A" in scratchpad.read("s_a")
    assert "belongs to A" not in scratchpad.read("s_b")


def test_session_id_is_sanitized_no_traversal():
    # A hostile id must not escape the scratchpad directory.
    scratchpad.add("../../evil", "should stay contained")
    path = scratchpad._path("../../evil")
    assert path.parent == scratchpad._DIR
    assert path.exists()


def test_scratchpad_lives_outside_session_dir(tmp_path):
    # The file must NOT be inside a session directory, so deleting the session
    # (which removes <base>/.tableint/sessions/<id>/) never touches the notes.
    from tabint import persistence

    session_dir = persistence.session_dir("s_x", base=tmp_path)
    pad = scratchpad._path("s_x")
    assert session_dir not in pad.parents
