"""src/loader.py の読み込みロジックに対するテスト。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.loader import LoaderError, load_cases, load_cases_from_records
from src.models import TestCase


def test_load_cases_empty_file_returns_empty_list(tmp_path: Path) -> None:
    """空ファイルは空リストを返し例外を投げない。"""
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    assert load_cases(empty) == []


def test_load_cases_missing_file_returns_empty_list(tmp_path: Path) -> None:
    """存在しないパスも空リスト。"""
    assert load_cases(tmp_path / "no_such.json") == []


def test_load_cases_csv_with_missing_columns(tmp_path: Path) -> None:
    """必須列が欠けても安全な既定値で読める。"""
    csv_path = tmp_path / "mini.csv"
    csv_path.write_text("case_id,new_output\nx1,hello\n", encoding="utf-8")
    cases = load_cases(csv_path)
    assert len(cases) == 1
    assert cases[0].case_id == "x1"
    assert cases[0].prompt_old == ""
    assert cases[0].new_output == "hello"


def test_load_cases_csv_splits_keywords(tmp_path: Path) -> None:
    """keywords/forbidden はカンマ区切りで分割される。"""
    csv_path = tmp_path / "kw.csv"
    csv_path.write_text(
        "case_id,expected_output,new_output,keywords,forbidden\n"
        'c1,期待,新,"請求","再発行,推測,恐らく"\n',
        encoding="utf-8",
    )
    cases = load_cases(csv_path)
    assert cases[0].keywords == ["請求"]
    assert cases[0].forbidden == ["再発行", "推測", "恐らく"]


def test_load_cases_json_array(tmp_path: Path) -> None:
    """トップレベル配列の JSON を読める。"""
    data = [
        {
            "case_id": "j1",
            "expected_output": "x",
            "new_output": "x",
            "keywords": ["a", "b"],
        }
    ]
    json_path = tmp_path / "arr.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")
    cases = load_cases(json_path)
    assert len(cases) == 1
    assert cases[0].keywords == ["a", "b"]


def test_load_cases_json_cases_wrapper(tmp_path: Path) -> None:
    """{'cases': [...]} 形式の JSON も読める。"""
    data = {"cases": [{"case_id": "j2", "new_output": "y"}]}
    json_path = tmp_path / "wrapped.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")
    cases = load_cases(json_path)
    assert cases[0].case_id == "j2"


def test_load_cases_unsupported_extension_raises(tmp_path: Path) -> None:
    """未対応拡張子は LoaderError。"""
    p = tmp_path / "data.txt"
    p.write_text("hello", encoding="utf-8")
    with pytest.raises(LoaderError):
        load_cases(p)


def test_load_cases_invalid_json_structure_raises(tmp_path: Path) -> None:
    """JSON が dict だが cases キーがない場合は LoaderError。"""
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"wrong": 1}), encoding="utf-8")
    with pytest.raises(LoaderError):
        load_cases(p)


def test_load_cases_from_records_handles_empty() -> None:
    """空リストからは空リスト。"""
    assert load_cases_from_records([]) == []


def test_load_cases_from_records_fallback_id() -> None:
    """case_id が無くてもフォールバックIDが付く。"""
    cases = load_cases_from_records([{"new_output": "a"}, {"new_output": "b"}])
    assert cases[0].case_id == "case-000"
    assert cases[1].case_id == "case-001"
    assert isinstance(cases[0], TestCase)
