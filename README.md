# Prompt Regression Tester

プロンプト変更の前後で出力品質が落ちたケース（regression）を検出する小型 Streamlit アプリ。
AI 機能の変更をテスト可能にすることを示すポートフォリオ作品。

## 目的

プロンプトを変更すると、一部ケースで出力が悪化することがある。このアプリは
旧プロンプトと新プロンプトの出力を並べ、期待出力に対するスコアの低下を可視化する。
外部 LLM API は使わず、固定のサンプル出力で動くので API キーなしで起動できる。

## 主要機能

- CSV または JSON からテストケースを読み込む
- 旧出力と新出力を比較し、以下を算出する
  - 文字列の完全一致（正規化後）
  - 期待出力との類似度（SequenceMatcher）
  - 期待キーワードの一致率と不足一覧
  - 禁止語の検出
- fail ケースを上位表示し、fail の理由を列挙する
- 旧・新出力の行単位差分を色付きで並列表示し、unified diff も展開可能

## 使用技術

- Python 3.11+
- Streamlit（UI）
- pandas（表示用データフレーム）
- 標準ライブラリ（difflib / csv / json / pathlib）

## データの出所

データはすべて合成（`sample_data/`）。架空の業務タスク（メール要約・カテゴリ分類・礼状作成・FAQ回答）を
人手で作ったもので、実在する LLM の出力ではない。将来 LLM API を統合する場合は環境変数からキーを読む前提だが、
本アプリはキー不要で動作する。

### テストケースの列

| 列 | 必須 | 説明 |
|---|---|---|
| `case_id` | 任意 | 無ければ `case-000` 等のフォールバックID |
| `task` | 任意 | 業務タスクの説明 |
| `prompt_old` | 推奨 | 旧プロンプト |
| `prompt_new` | 推奨 | 新プロンプト |
| `expected_output` | 推奨 | 期待出力 |
| `old_output` | 推奨 | 旧プロンプトでの出力 |
| `new_output` | 推奨 | 新プロンプトでの出力 |
| `keywords` | 任意 | カンマ区切りの期待キーワード |
| `forbidden` | 任意 | カンマ区切りの禁止語 |

JSON の場合は `keywords` / `forbidden` を配列でも書ける。トップレベルは配列か `{"cases": [...]}`。

## ローカル実行手順

```bash
cd prompt-regression-tester
python -m venv .venv && source .venv/bin/activate   # 任意
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

ブラウザが開く。サイドバーで「サンプル (CSV)」か「サンプル (JSON)」を選ぶか、
自分の CSV/JSON をアップロードする。類似度の fail 閾値はスライダーで調整できる。

### テスト

```bash
pip install -r requirements.txt   # pytest 含む
pytest
```

`src/` の採点・読み込み・差分ヘルパに対する単体テストと、サンプルデータの統合テストが走る。

## プロジェクト構成

```
prompt-regression-tester/
├── app/streamlit_app.py     # UI（表示のみ・ロジックは src/ へ委譲）
├── src/
│   ├── models.py            # TestCase / CaseScore データモデル
│   ├── loader.py            # CSV/JSON 読み込み（欠損列・空ファイル対応）
│   ├── scorer.py            # 採点ロジック（一致・類似度・キーワード・禁止語）
│   └── comparator.py        # 差分表示ヘルパ
├── tests/                   # pytest
├── sample_data/             # 合成サンプル（CSV/JSON）
├── assets/                  # スクショ置き場
└── requirements.txt
```

## スクショ

スクリーンショットは `assets/` に配置する（現在は空）。

## 制限事項

- MVP であり、認証・DB・本番運用機能・課金は含まない
- 外部 LLM API を呼ばない。出力は固定サンプル
- 合成テストケースであり、実在の LLM 品質を保証しない
- 類似度は SequenceMatcher ベースの文字列表面的な指標であり、意味的妥当性は評価しない
