# paper-to-notion

arXivからキーワード・日付範囲で論文を収集し、Notionに保存するツール。

----

## 1. 要件
- キーワード：ユーザーがGUIから設定。保存チェックボックスを押すと、yamlファイルに保存し、次回起動時に自動的に読み込まれる。
- 調査数：ユーザーがGUIから設定。デフォルトは5。スライドボタンとテキストボックスで設定。
- 日付範囲：ユーザーがGUIから設定。デフォルトは過去１年間。
- データソース：arXiv
- 収集対象フィールド：タイトル、URL、著者、公開日、カテゴリ、abstract
- 出力：GUIにタイトル、日時、abstractを表示。
- abstractの翻訳：ローカルLM（Swallow MS）で日本語に翻訳。
- Notionへの保存：左側のチェックボックスにチェックを入れた論文のみNotionに保存する。
- NotionのDB：ユーザーがGUIから設定。もし存在しない場合は新規作成する。

## 2. GUI構成
- CustomTkinterを使用したGUI。
- キーワード入力欄：テキストボックス。
- 調査数：スライドボタンとテキストボックス。
- 日付範囲
- NotionのDB：テキストボックス or ドロップダウンメニュー。
- 論文の表示：それぞれの論文のタイトル、日時、abstractを表示。左側にチェックボックスを配置。
- 読み込み中：読み込み中の表示。

## 3. データモデル
```python
class Paper(BaseModel):
    title: str
    url: str
    authors: List[str]
    published_date: str
    category: str
    abstract: str
    abstract_ja: str
```

## 4. アーキテクチャ
### MVCパターンに準拠
- **Model**: `src/domain/models.py` データ構造定義
- **View**: `src/app/ui/views/` 画面レイアウト
- **Controller**: `src/app/controller.py` アプリケーションロジック

## 5. フォルダ構成
```
paper-to-notion/
├── src/
│   ├── app/                  # アプリケーション層
│   │   ├── main.py           # エントリポイント
│   │   ├── app_window.py     # メインウィンドウ管理
│   │   └── controller.py     # アプリケーションロジック
│   ├── ui/                   # GUIコンポーネント層 (新規追加)
│   │   ├── components/       # 再利用可能コンポーネン
│   │   │   ├── header.py
│   │   │   ├── paper_list.py
│   │   │   ├── search_bar.py
│   │   │   └── ...
│   │   └── views/            # 画面レイアウト
│   │       ├── main_view.py
│   │       ├── settings_view.py
│   │       └── ...
│   ├── domain/               # ドメインモデル
│   ├── services/             # ビジネスロジック
│   └── utils/                # 共通ユーティリティ
├── tests/
│   ├── unit/
│   │   ├── test_arxiv.py
│   │   ├── test_notion.py
│   │   └── test_utils.py
│   └── integration/          # 統合テスト用
├── config/                   # 設定ファイル
│   └── keywords.yaml         # 保存されたキーワード
├── data/                     # 生成データ
│   └── papers.json           # 一時保存論文データ
├── logs/                     # ログファイル（自動生成）
├── .gitignore
├── README.md
└── requirements.txt

## 起動方法

```bash
uvicorn run python src/main.py