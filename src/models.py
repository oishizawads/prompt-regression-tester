"""テストケースとスコアのデータモデル。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class TestCase:
    """1件のプロンプト回帰テストケース。"""

    __test__ = False  # pytest がテストクラスと誤認するのを防ぐ

    case_id: str
    task: str
    prompt_old: str
    prompt_new: str
    expected_output: str
    old_output: str
    new_output: str
    keywords: list[str] = field(default_factory=list)
    forbidden: list[str] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: dict, index: int) -> "TestCase":
        """辞書1行から TestCase を生成する。欠損列は安全な既定値で補う。

        Args:
            row: 読み込み元の1行分の辞書。
            index: 行番号ベースのフォールバックID。

        Returns:
            TestCase インスタンス。
        """
        def _split(value: object) -> list[str]:
            """カンマ区切りまたはリスト値をキーワード/禁止語リストへ分解する。"""
            if isinstance(value, list):
                return [str(v).strip() for v in value if str(v).strip()]
            if not isinstance(value, str) or not value.strip():
                return []
            return [v.strip() for v in value.split(",") if v.strip()]

        return cls(
            case_id=str(row.get("case_id") or row.get("id") or f"case-{index:03d}"),
            task=str(row.get("task") or ""),
            prompt_old=str(row.get("prompt_old") or row.get("prompt_old_text") or ""),
            prompt_new=str(row.get("prompt_new") or row.get("prompt_new_text") or ""),
            expected_output=str(row.get("expected_output") or ""),
            old_output=str(row.get("old_output") or ""),
            new_output=str(row.get("new_output") or ""),
            keywords=_split(row.get("keywords")),
            forbidden=_split(row.get("forbidden")),
        )


@dataclass
class CaseScore:
    """1ケース分の採点結果。"""

    case_id: str
    exact_match: bool
    similarity: float
    keyword_hit_rate: float
    keyword_misses: list[str]
    forbidden_hits: list[str]
    is_fail: bool
    reasons: list[str]


def collect_failure_reasons(
    forbidden_hits: Sequence[str],
    keyword_misses: Sequence[str],
    similarity: float,
    threshold: float,
) -> list[str]:
    """fail 判定理由を人間可読で列挙する。"""
    reasons: list[str] = []
    if forbidden_hits:
        reasons.append(f"禁止語が含まれる: {', '.join(forbidden_hits)}")
    if keyword_misses:
        reasons.append(f"期待キーワード不足: {', '.join(keyword_misses)}")
    if similarity < threshold:
        reasons.append(f"類似度が閾値未満: {similarity:.2f} < {threshold:.2f}")
    return reasons
