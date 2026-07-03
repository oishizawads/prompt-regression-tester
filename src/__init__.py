"""prompt-regression-tester の計算ロジックパッケージ。"""

from .comparator import changed_line_indices, side_by_side, unified_diff_lines
from .loader import LoaderError, load_cases, load_cases_from_records
from .models import CaseScore, TestCase
from .scorer import (
    DEFAULT_SIMILARITY_THRESHOLD,
    exact_match,
    forbidden_matches,
    keyword_matches,
    normalize,
    score_case,
    score_cases,
    similarity,
)

__all__ = [
    "CaseScore",
    "DEFAULT_SIMILARITY_THRESHOLD",
    "LoaderError",
    "TestCase",
    "changed_line_indices",
    "exact_match",
    "forbidden_matches",
    "keyword_matches",
    "load_cases",
    "load_cases_from_records",
    "normalize",
    "score_case",
    "score_cases",
    "side_by_side",
    "similarity",
    "unified_diff_lines",
]
