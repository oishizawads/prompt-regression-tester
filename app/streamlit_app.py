"""prompt-regression-tester の Streamlit エントリポイント。

計算ロジックは src/ に委譲し、このファイルは表示のみを担う。
実行: streamlit run app/streamlit_app.py （API キー不要）
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src import (  # noqa: E402
    DEFAULT_SIMILARITY_THRESHOLD,
    LoaderError,
    TestCase,
    changed_line_indices,
    load_cases,
    load_cases_from_records,
    score_cases,
    side_by_side,
    unified_diff_lines,
)

_SAMPLE_CSV = _REPO_ROOT / "sample_data" / "sample_cases.csv"
_SAMPLE_JSON = _REPO_ROOT / "sample_data" / "sample_cases.json"


def _cases_to_records(cases: list[TestCase]) -> list[dict]:
    """UI 表示用に TestCase リストを dict 行へ戻す。"""
    return [
        {
            "case_id": c.case_id,
            "task": c.task,
            "prompt_old": c.prompt_old,
            "prompt_new": c.prompt_new,
            "expected_output": c.expected_output,
            "old_output": c.old_output,
            "new_output": c.new_output,
            "keywords": ",".join(c.keywords),
            "forbidden": ",".join(c.forbidden),
        }
        for c in cases
    ]


def _render_diff(case: TestCase) -> None:
    """旧・新を並列表示し、変更行を強調する。"""
    old_lines, new_lines = side_by_side(case)
    changed = set(changed_line_indices(case))
    if not old_lines and not new_lines:
        st.caption("出力が空のため差分なし")
        return
    cols = st.columns(2)
    with cols[0]:
        st.markdown("**旧出力 (old)**")
        for i, line in enumerate(old_lines):
            style = "background:#3a1f1f;" if i in changed else ""
            st.markdown(
                f'<div style="{style}padding:2px 6px;border-radius:4px;'
                f'white-space:pre-wrap;font-family:monospace;">'
                f'{line if line else " "}</div>',
                unsafe_allow_html=True,
            )
    with cols[1]:
        st.markdown("**新出力 (new)**")
        for i, line in enumerate(new_lines):
            style = "background:#1f3a1f;" if i in changed else ""
            st.markdown(
                f'<div style="{style}padding:2px 6px;border-radius:4px;'
                f'white-space:pre-wrap;font-family:monospace;">'
                f'{line if line else " "}</div>',
                unsafe_allow_html=True,
            )
    with st.expander("unified diff", expanded=False):
        diff = unified_diff_lines(case)
        st.code("\n".join(diff), language="diff")


def _load_cases_from_input(uploaded, source: str) -> list[TestCase]:
    """入力ソース種別に応じて TestCase リストを組み立てる。エラーは表示して空リストへ。"""
    if source == "サンプル (CSV)":
        return load_cases(_SAMPLE_CSV)
    if source == "サンプル (JSON)":
        return load_cases(_SAMPLE_JSON)
    if uploaded is None:
        return []
    suffix = Path(uploaded.name).suffix.lower()
    if suffix not in {".csv", ".json"}:
        st.error("対応形式は .csv または .json です")
        return []
    raw = uploaded.getvalue().decode("utf-8")
    if not raw.strip():
        return []
    tmp = _REPO_ROOT / ".tmp_upload" / uploaded.name
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(raw, encoding="utf-8")
    try:
        return load_cases(tmp)
    except LoaderError as e:
        st.error(f"読み込みエラー: {e}")
        return []
    finally:
        if tmp.exists():
            tmp.unlink()


def main() -> None:
    """アプリ本体。UI と状態管理のみ。"""
    st.set_page_config(
        page_title="Prompt Regression Tester",
        page_icon="🧪",
        layout="wide",
    )
    st.title("🧪 Prompt Regression Tester")
    st.caption(
        "プロンプト変更の前後で出力品質が落ちたケース（regression）を検出します。"
        "データは合成サンプルであり、実在の LLM 品質を保証するものではありません。"
    )

    with st.sidebar:
        st.header("設定")
        source = st.radio(
            "データソース",
            ["サンプル (CSV)", "サンプル (JSON)", "ファイルをアップロード"],
            index=0,
        )
        uploaded = (
            st.file_uploader(
                "CSV または JSON を選択",
                type=["csv", "json"],
                accept_multiple_files=False,
            )
            if source == "ファイルをアップロード"
            else None
        )
        threshold = st.slider(
            "類似度 fail 閾値",
            min_value=0.0,
            max_value=1.0,
            value=float(DEFAULT_SIMILARITY_THRESHOLD),
            step=0.05,
            help="新出力と期待出力の類似度がこれ未満だと fail にします",
        )
        if st.button("データを再読み込み", use_container_width=True):
            st.session_state["reload_nonce"] = st.session_state.get("reload_nonce", 0) + 1
        st.session_state.setdefault("reload_nonce", 0)

    cases = _load_cases_from_input(uploaded, source)

    if not cases:
        st.info(
            "テストケースがありません。サンプルを選択するか、CSV/JSON をアップロードしてください。"
            " 列: case_id, task, prompt_old, prompt_new, expected_output, old_output, "
            "new_output, keywords(任意), forbidden(任意)"
        )
        st.stop()

    records = _cases_to_records(cases)
    df = pd.DataFrame(records)
    scores = score_cases(cases, similarity_threshold=threshold)
    score_df = pd.DataFrame(
        [
            {
                "case_id": s.case_id,
                "exact_match": s.exact_match,
                "similarity": s.similarity,
                "keyword_hit_rate": s.keyword_hit_rate,
                "forbidden_hits": ", ".join(s.forbidden_hits),
                "is_fail": s.is_fail,
                "reasons": " / ".join(s.reasons) if s.reasons else "—",
            }
            for s in scores
        ]
    )

    fail_n = int(score_df["is_fail"].sum())
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("テストケース数", len(cases))
    col_b.metric("fail", fail_n)
    col_c.metric("pass", len(cases) - fail_n)

    st.subheader("スコア比較（fail を上位表示）")
    st.dataframe(
        score_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "is_fail": st.column_config.CheckboxColumn("fail", disabled=True),
            "similarity": st.column_config.NumberColumn("類似度", format="%.3f"),
            "keyword_hit_rate": st.column_config.NumberColumn(
                "キーワード一致率", format="%.3f"
            ),
        },
    )

    st.subheader("テストケース一覧")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("ケース詳細")
    options = [c.case_id for c in cases]
    selected_id = st.selectbox("ケースを選択", options, index=0)
    selected = next((c for c in cases if c.case_id == selected_id), None)
    if selected is None:
        st.warning("選択したケースが見つかりません")
        st.stop()
    sel_score = next((s for s in scores if s.case_id == selected_id), None)

    left, right = st.columns(2)
    with left:
        st.markdown("**旧プロンプト**")
        st.text_area(
            "old_prompt",
            value=selected.prompt_old,
            height=120,
            label_visibility="collapsed",
        )
    with right:
        st.markdown("**新プロンプト**")
        st.text_area(
            "new_prompt",
            value=selected.prompt_new,
            height=120,
            label_visibility="collapsed",
        )

    st.markdown("**期待出力**")
    st.text_area(
        "expected",
        value=selected.expected_output,
        height=100,
        label_visibility="collapsed",
    )

    if sel_score is not None:
        if sel_score.is_fail:
            st.error(
                "FAIL — " + (" / ".join(sel_score.reasons) if sel_score.reasons else "条件未達")
            )
        else:
            st.success("PASS")

    st.markdown("**差分（旧 vs 新 出力）**")
    _render_diff(selected)

    st.caption(
        "合成テストケースであり実在の LLM 品質を保証しない / API キー不要で動作"
    )


if __name__ == "__main__":
    main()
