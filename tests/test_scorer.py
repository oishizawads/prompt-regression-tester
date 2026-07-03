"""src/scorer.py の採点ロジックに対するテスト。"""

from __future__ import annotations

from src.models import TestCase
from src.scorer import (
    exact_match,
    forbidden_matches,
    keyword_matches,
    normalize,
    score_case,
    score_cases,
    similarity,
)


def test_normalize_compress_whitespace_and_lowercase() -> None:
    """正規化は空白圧縮と小文字化を行う。"""
    assert normalize("  Hello   World  ") == "hello world"


def test_similarity_identical_strings_returns_one() -> None:
    """同一文字列の類似度は1.0。"""
    assert similarity("同じ文章", "同じ文章") == 1.0


def test_similarity_empty_strings_returns_one() -> None:
    """両方空文字の類似度は1.0とみなす。"""
    assert similarity("", "") == 1.0


def test_similarity_one_empty_returns_zero() -> None:
    """片方だけ空なら類似度0.0。"""
    assert similarity("abc", "") == 0.0
    assert similarity("", "abc") == 0.0


def test_exact_match_ignores_whitespace_and_case() -> None:
    """完全一致は空白・大文字小文字を無視する。"""
    assert exact_match("ABC  DE", "abc de") is True
    assert exact_match("abc", "abd") is False


def test_keyword_matches_normalizes() -> None:
    """キーワード一致は正規化して判定する。"""
    assert keyword_matches("返品期限は14日", ["返品", "14日"]) == ["返品", "14日"]
    assert keyword_matches("別の話題です", ["返品"]) == []


def test_forbidden_matches_detects_banned_words() -> None:
    """禁止語は含まれたものだけ返す。"""
    assert forbidden_matches("推測ですが返品の可能性", ["推測", "可能性", "思う"]) == [
        "推測",
        "可能性",
    ]


def _make_case(**overrides) -> TestCase:
    """テスト用 TestCase を組むヘルパー。"""
    base = dict(
        case_id="t1",
        task="テスト",
        prompt_old="old",
        prompt_new="new",
        expected_output="期待",
        old_output="旧",
        new_output="新",
        keywords=[],
        forbidden=[],
    )
    base.update(overrides)
    return TestCase(**base)


def test_score_case_pass_when_exact_and_no_forbidden() -> None:
    """完全一致かつ禁止語なしは PASS。"""
    case = _make_case(expected_output="請求", new_output="請求")
    score = score_case(case)
    assert score.is_fail is False
    assert score.exact_match is True
    assert score.similarity == 1.0
    assert score.reasons == []


def test_score_case_fail_when_forbidden_present() -> None:
    """禁止語が含まれると fail し、理由に禁止語が載る。"""
    case = _make_case(
        expected_output="請求",
        new_output="請求（推測）",
        forbidden=["推測"],
    )
    score = score_case(case)
    assert score.is_fail is True
    assert "推測" in score.forbidden_hits
    assert any("禁止語" in r for r in score.reasons)


def test_score_case_fail_when_keyword_missing() -> None:
    """期待キーワードが欠けると fail する。"""
    case = _make_case(
        expected_output="請求書の金額誤り",
        new_output="金額が違う",
        keywords=["請求書", "再発行"],
    )
    score = score_case(case)
    assert score.is_fail is True
    assert "請求書" in score.keyword_misses
    assert score.keyword_hit_rate < 1.0


def test_score_case_fail_when_similarity_below_threshold() -> None:
    """類似度が閾値未満だと fail する。"""
    case = _make_case(
        expected_output="返品期限は14日です未開封が条件です",
        new_output="全く違う内容の文章です",
        keywords=[],
    )
    score = score_case(case, similarity_threshold=0.5)
    assert score.is_fail is True
    assert score.similarity < 0.5


def test_score_cases_sorts_fail_first() -> None:
    """score_cases は fail を先頭に並べる。"""
    pass_case = _make_case(case_id="p1", expected_output="ok", new_output="ok")
    fail_case = _make_case(case_id="f1", expected_output="ok", new_output="ng", forbidden=["ng"])
    scores = score_cases([pass_case, fail_case])
    assert scores[0].is_fail is True
    assert scores[1].is_fail is False


def test_keyword_hit_rate_one_when_no_keywords() -> None:
    """キーワード未指定時の hit_rate は1.0（ペナルティなし）。"""
    case = _make_case(expected_output="x", new_output="y", keywords=[])
    score = score_case(case)
    assert score.keyword_hit_rate == 1.0
