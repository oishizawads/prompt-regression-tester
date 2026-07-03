"""src/comparator.py の差分ヘルパに対するテスト。"""

from __future__ import annotations

from src.comparator import changed_line_indices, side_by_side, unified_diff_lines
from src.models import TestCase


def _make_case(old_output: str, new_output: str) -> TestCase:
    return TestCase(
        case_id="c1",
        task="t",
        prompt_old="",
        prompt_new="",
        expected_output="",
        old_output=old_output,
        new_output=new_output,
    )


def test_side_by_side_pads_shorter_side() -> None:
    """行数が違うとき短い側を空行で埋める。"""
    old_lines, new_lines = side_by_side(_make_case("a\nb", "a"))
    assert len(old_lines) == len(new_lines) == 2
    assert new_lines[1] == ""


def test_changed_line_indices_flags_diff_rows() -> None:
    """差がある行番号だけを返す。"""
    case = _make_case("a\nb\nc", "a\nB\nc")
    assert changed_line_indices(case) == [1]


def test_unified_diff_lines_includes_headers() -> None:
    """unified diff にファイル名ヘッダが含まれる。"""
    diff = unified_diff_lines(_make_case("a", "b"))
    joined = "\n".join(diff)
    assert "c1.old" in joined
    assert "c1.new" in joined


def test_changed_line_indices_empty_outputs() -> None:
    """両方空のとき変更行は無し。"""
    assert changed_line_indices(_make_case("", "")) == []
