"""テストケースの読み込み（CSV / JSON / 辞書リスト）。"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .models import TestCase


class LoaderError(ValueError):
    """読み込み時の軽微な問題を表す例外（空ファイル・未対応形式など）。"""


def _load_rows_from_csv(path: Path) -> list[dict]:
    """CSV ファイルを dict 行リストへ読み込む。"""
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows


def _load_rows_from_json(path: Path) -> list[dict]:
    """JSON ファイルを dict 行リストへ読み込む（配列または {"cases":[...]} を許容）。"""
    with path.open("r", encoding="utf-8") as f:
        data: Any = json.load(f)
    if isinstance(data, dict) and "cases" in data:
        data = data["cases"]
    if not isinstance(data, list):
        raise LoaderError("JSON のトップレベルは配列か {'cases': [...]} が必要です")
    return [row if isinstance(row, dict) else {"raw": row} for row in data]


def load_cases(path: Path) -> list[TestCase]:
    """ファイルパスから TestCase リストを生成する。

    Args:
        path: CSV または JSON ファイルへのパス。

    Returns:
        TestCase リスト。空ファイル・欠損列でも空リストを返し例外は投げない。

    Raises:
        LoaderError: 拡張子未対応・JSON 構造不正のとき。
    """
    if not path.exists() or path.stat().st_size == 0:
        return []
    suffix = path.suffix.lower()
    if suffix == ".csv":
        rows = _load_rows_from_csv(path)
    elif suffix == ".json":
        rows = _load_rows_from_json(path)
    else:
        raise LoaderError(f"未対応の拡張子です: {suffix}（.csv または .json を指定）")
    return [TestCase.from_row(row, idx) for idx, row in enumerate(rows)]


def load_cases_from_records(records: list[dict]) -> list[TestCase]:
    """メモリ上の辞書リストから TestCase リストを生成する（UI 入力用）。"""
    return [TestCase.from_row(row, idx) for idx, row in enumerate(records)]
