# paper-to-notion
論文を調査してNotionに記録するアプリ
> 目的: 毎日、指定キーワードで **arXiv**を収集し、結果を **Notion** に保存する。学習しながら実装・拡張しやすい構成を採用。

---

## 1. 要件（Requirements）

* **キーワード**: ユーザー設定可能（複数対応）。
* **データソース**:

  * arXiv（当日分 / JST）
* **和訳**: ローカルLLM（Swallow MS）。
* **出力**: どのNotion DBに保存するかは設定可能。もし、存在しない場合は新規作成。
* **時刻/タイムゾーン**: JST基準で「今日」。
* **重複排除**: URL正規化による重複除去（クエリ・フラグメントの正規化）。
* **運用**: ログ、失敗時の縮退運転、レート制限、robots.txt尊重、ETag/Last‑Modifiedキャッシュ。

---

## 2. システム構成（Architecture）

```
            +----------------- Config/Secrets (.env / CLI / pydantic-settings)
            |
+-----------v-----------+        +---------------------+     +-----------------+     +------------------+
|  Orchestrator (UseCase) +------>  Fetcher (HTTP) +----->  Extractor      +----->  Summarizer (LLM) |
|  収集→要約→保存        |        |  requests + cache   |     |  trafilatura→    |     |  llama.cpp       |
+-----------+-----------+        |  robots + retry      |     |  readability→   |     |  map-reduce      |
            |                    +-----+-----------+----+     |  newspaper3k    |     +--------+---------+
            |                          |           |          +--------+--------+              |
            |                          |           |                   |                       |
            v                          v           v                   v                       v
      Collectors (arXiv,RSS)     Robots checker   Cache         Cleaner/Segmenter          Sinks (Notion/MD)
      URL/メタ収集 → 正規化        尊重/制御       ETag等         言語/段落整形               ログ/メトリクス
```

### レイヤ別責務

* **Collectors**: arXiv からタイトル・URL・公開日時などのメタを取得。
* **HTML Fetcher**: User‑Agent明示、robots遵守、タイムアウト/リトライ、ETag/Last‑Modified対応、簡易ディスクキャッシュ。
* **Extractor**: trafilatura を既定、失敗時は readability‑lxml → newspaper3k の多段フォールバック。本文の品質チェック（最小文字数/段落数）。
* **NLP Utilities**: クリーニング、言語判定、チャンク分割（文字/文ベース）など。
* **Summarizer**: llama.cpp（OpenAI互換API）または llama‑cpp‑python をバックエンドに、map→reduce の二段要約。出力はMarkdown＋出典リンク。
* **Sinks**: Notion API（ページ作成/更新）、ローカルMarkdown/JSON。

---

## 3. データモデル（Domain Models）

```python
Source = Literal["arxiv", "news"]

class Item(BaseModel):
    source: Source
    keyword: str
    title: str
    url: HttpUrl
    published_at: datetime
    summary_raw: str | None = None  # arXiv abstract 等
    authors: list[str] | None = None

class Article(BaseModel):
    source_url: HttpUrl
    title: str
    byline: str | None
    published_at: datetime | None
    text: str  # 抽出済み本文（プレーンテキスト）
    lang: str | None

class SummarySection(BaseModel):
    title: str  # 例: 「今日のニュース（本文要約）」
    markdown: str

class RunResult(BaseModel):
    date_label: str
    counts: dict  # {"arxiv": int, "news": int, "extracted": int}
    sections: list[SummarySection]
```

---

## 4. フォルダ構成（Project Layout）

```
daily_summarizer/
├─ src/
│  ├─ app/
│  │  ├─ orchestrator.py          # 収集→抽出→要約→保存のユースケース
│  │  └─ cli.py                   # CLI エントリ
│  ├─ config/
│  │  └─ settings.py              # 環境変数/CLI/デフォルトの統合
│  ├─ collectors/
│  │  ├─ arxiv.py                 # arXiv メタ取得
│  │  └─ news_rss.py              # RSS → URL収集
│  ├─ fetch/
│  │  ├─ http.py                  # requests + retry + timeout + UA
│  │  ├─ robots.py                # robots.txt の確認
│  │  └─ cache.py                 # ETag/Last-Modified/ディスクキャッシュ
│  ├─ extract/
│  │  ├─ base.py
│  │  ├─ trafilatura_extractor.py
│  │  ├─ readability_extractor.py
│  │  └─ newspaper_extractor.py
│  ├─ nlp/
│  │  ├─ clean.py
│  │  ├─ segment.py
│  │  └─ lang.py
│  ├─ summarizers/
│  │  ├─ base.py
│  │  ├─ llama_server.py          # OpenAI互換APIクライアント
│  │  └─ llama_cpp_local.py       # 直接呼び出し
│  ├─ sinks/
│  │  ├─ base.py
│  │  ├─ notion.py
│  │  └─ markdown.py
│  ├─ domain/
│  │  ├─ models.py
│  │  └─ prompts.py
│  ├─ utils/
│  │  ├─ url.py
│  │  ├─ time.py
│  │  └─ logging.py
│  └─ __init__.py
├─ tests/
│  ├─ test_extract_trafilatura.py
│  ├─ test_fetch_http.py
│  ├─ test_orchestrator.py
│  └─ data/                       # サンプルHTML/RSS
├─ .env.example
├─ requirements.txt or pyproject.toml
└─ README.md
```

---

## 5. ワークフロー（Use‑case Flow）

1. **Collect**: arXiv & RSS から (title, url, published\_at, keyword) を収集。
2. **Normalize**: URL正規化・重複排除・JST「当日」フィルタ。
3. **Fetch**: robots.txtを確認し、HTML取得（ETag/If‑Modified‑Since対応、timeout/retry）。
4. **Extract**: trafilatura → readability → newspaper の順で本文抽出。閾値未満なら次段へフォールバック。
5. **Segment & Clean**: 言語判定、段落整形、チャンク分割（例: 1,200〜1,600文字, overlap 120）。
6. **Summarize (map‑reduce)**: mapで各チャンク要約、reduceで統合。Markdown＋出典リンクを生成。
7. **Sink**: Notionページ「リサーチログ YYYY‑MM‑DD」を作成/更新（idempotent）。同時に `/out/YYYY‑MM‑DD.md` に保存可能。

---

## 6. 設定（Settings）

* `KEYWORDS`: カンマ区切り/CLI引数。
* `NEWS_RSS_MAX_PER_KW`: RSS上限。
* `FETCH_TIMEOUT_SEC`, `RETRY_MAX`, `RATE_LIMIT_RPS`。
* `ROBOT_POLICY`: `"respect"`（既定） / `"ignore"`。
* `EXTRACTOR_ORDER`: `["trafilatura","readability","newspaper3k"]`。
* `CHUNK_CHARS`, `OVERLAP_CHARS`, `MODEL_CTX`, `MAX_NEW_TOKENS`。
* `LLM_BACKEND`: `"llama_server"` / `"llama_cpp"`。
* `NOTION_TOKEN`, `NOTION_DATABASE_ID`。

`.env.example` に雛形を同梱。

---

## 7. エラー処理・縮退運転（Resilience）

* Fetch失敗: リトライ（指数バックオフ）→キャッシュ/スキップ。
* Extract失敗: 次フォールバックへ。最終的に `og:description` 等で仮本文。
* Summarize失敗: 短い「仮要約」（先頭数段落＋タイトル）を生成し処理継続。
* Notion失敗: ローカルMarkdown/JSONに退避し、次回Sync対象としてキュー化。

---

## 8. テスト（Testing）

* **Unit**: Extractor（固定HTMLで本文率を検証）、Fetcher（304/ETag/timeout/ retry）、Summarizer（ダミーバックエンド）。
* **E2E (Small)**: 小さなRSSサンプル → 2〜3記事 → Notion書き込みまで。
* **Deterministicモード**: LLMをダミーに切替えてスナップショットテストを可能に。

---

## 9. 実装順序（Milestones）

1. Collectors + 正規化/重複排除 + JSTフィルタ → JSON出力
2. Fetch + robots + キャッシュ → HTML保存
3. Extract（多段）+ Clean + Segment → テキスト化
4. Summarizer（ダミー→llama\_server）→ Markdown化
5. Notion Sink → idempotent更新
6. 失敗時縮退/ログ/テスト拡充 → Docker/cron

---

## 10. 伸びしろ（Future Work）

* 見出し抽出・要点抽出（キーフレーズ/エンティティ）
* 重要度スコアリング（相対/時系列）
* マルチメディア（PDF/図表）への対応
* PlaywrightによるJSレンダリング（必要時のみ）
* プロンプトの自動評価（文字数・論理構造チェック）

---

## 11. 実行例（CLI）

```bash
python -m src.app.cli \
  --keywords "LLM,マルチモーダル,強化学習" \
  --llm-backend llama_server \
  --model-path ./models/mistral-7b-instruct.Q4_K_M.gguf
```

> これをベースにスターターコード（空実装のinterface + テスト雛形）を追加できます。必要なら次のステップで生成します。
