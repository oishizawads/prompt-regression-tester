"""旧出力と新出力の差分表示用ヘルパ。"""

from __future__ import annotations

import difflib

from .models import TestCase


def unified_diff_lines(case: TestCase) -> list[str]:
    """旧出力と新出力の unified diff を行リストで返す。"""
    old_lines = case.old_output.splitlines() or [case.old_output]
    new_lines = case.new_output.splitlines() or [case.new_output]
    return list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"{case.case_id}.old",
            tofile=f"{case.case_id}.new",
            lineterm="",
        )
    )


def side_by_side(case: TestCase) -> tuple[list[str], list[str]]:
    """旧・新を並べて比較しやすいよう行リストを返す（長さは揃える）。"""
    old_lines = case.old_output.splitlines() or [case.old_output]
    new_lines = case.new_output.splitlines() or [case.new_output]
    n = max(len(old_lines), len(new_lines))
    old_padded = old_lines + [""] * (n - len(old_lines))
    new_padded = new_lines + [""] * (n - len(new_lines))
    return old_padded, new_padded


def changed_line_indices(case: TestCase) -> list[int]:
    """旧・新で内容が異なる行番号（0始まり）を返す。"""
    old_lines, new_lines = side_by_side(case)
    return [i for i, (o, n) in enumerate(zip(old_lines, new_lines)) if o != n]
