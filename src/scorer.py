"""採点ロジック（文字列一致・キーワード一致・禁止語検出）。"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from .models import CaseScore, TestCase, collect_failure_reasons

DEFAULT_SIMILARITY_THRESHOLD = 0.6


def normalize(text: str) -> str:
    """比較前に文字列を正規化する（小文字化・連続空白の圧縮・前後空白除去）。"""
    if not text:
        return ""
    lowered = text.lower()
    collapsed = re.sub(r"\s+", " ", lowered)
    return collapsed.strip()


def similarity(a: str, b: str) -> float:
    """正規化後の2文字列の類似度を 0.0–1.0 で返す。"""
    na, nb = normalize(a), normalize(b)
    if not na and not nb:
        return 1.0
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def exact_match(a: str, b: str) -> bool:
    """正規化後の完全一致。"""
    return normalize(a) == normalize(b)


def keyword_matches(text: str, keywords: list[str]) -> list[str]:
    """キーワードのうち text に含まれるものを返す（正規化比較）。"""
    norm_text = normalize(text)
    return [kw for kw in keywords if kw and normalize(kw) in norm_text]


def forbidden_matches(text: str, forbidden: list[str]) -> list[str]:
    """禁止語のうち text に含まれるものを返す（正規化比較）。"""
    norm_text = normalize(text)
    return [w for w in forbidden if w and normalize(w) in norm_text]


def score_case(
    case: TestCase,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> CaseScore:
    """1ケースを旧・新それぞれで採点し、新出力ベースで fail 判定する。

    Args:
        case: 採点対象の TestCase。
        similarity_threshold: これ未満の類似度は fail 要因とする。

    Returns:
        CaseScore インスタンス。理由は人間可読で reasons に格納。
    """
    sim_new = similarity(case.expected_output, case.new_output)
    exact = exact_match(case.expected_output, case.new_output)
    kws = case.keywords
    hit_kws = keyword_matches(case.new_output, kws)
    miss_kws = [kw for kw in kws if kw not in hit_kws]
    hit_rate = (len(hit_kws) / len(kws)) if kws else 1.0
    forbids = forbidden_matches(case.new_output, case.forbidden)

    is_fail = bool(forbids) or hit_rate < 1.0 or sim_new < similarity_threshold
    reasons = collect_failure_reasons(forbids, miss_kws, sim_new, similarity_threshold)

    return CaseScore(
        case_id=case.case_id,
        exact_match=exact,
        similarity=round(sim_new, 3),
        keyword_hit_rate=round(hit_rate, 3),
        keyword_misses=miss_kws,
        forbidden_hits=forbids,
        is_fail=is_fail,
        reasons=reasons,
    )


def score_cases(
    cases: list[TestCase],
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> list[CaseScore]:
    """複数ケースを一括採点し、fail を先頭に安定ソートして返す。"""
    scores = [score_case(c, similarity_threshold) for c in cases]
    scores.sort(key=lambda s: (s.is_fail, s.case_id), reverse=True)
    return scores
