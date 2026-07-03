"""同梱サンプルデータが仕様通り読めることを確認する統合テスト。"""

from __future__ import annotations

from pathlib import Path

from src.loader import load_cases
from src.scorer import score_cases

_REPO_ROOT = Path(__file__).resolve().parent.parent


def test_sample_csv_loads_and_has_failures() -> None:
    """サンプルCSVは4ケースあり、fail が1件以上含まれる。"""
    cases = load_cases(_REPO_ROOT / "sample_data" / "sample_cases.csv")
    assert len(cases) == 4
    scores = score_cases(cases)
    assert any(s.is_fail for s in scores)


def test_sample_json_loads_and_has_failures() -> None:
    """サンプルJSONも同様に読めて fail を含む。"""
    cases = load_cases(_REPO_ROOT / "sample_data" / "sample_cases.json")
    assert len(cases) == 4
    scores = score_cases(cases)
    assert any(s.is_fail for s in scores)
