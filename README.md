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
- 調査中：読み込み中の表示。

## 3. データモデル
```python
class Paper:
    def __init__(self, title, url, authors, published_date, category, abstract):
        self.title = title
        self.url = url
        self.authors = authors
        self.published_date = published_date
        self.category = category
        self.abstract = abstract
```

## 4. フォルダ構成
```
paper-to-notion/
├── src/
│   ├── app/                  # アプリケーション層
│   │   ├── gui.py            # GUIメイン
│   │   └── main.py           # エントリポイント
│   ├── domain/               # ドメインモデル
│   │   └── models.py         # Paperクラスなど
│   ├── services/             # ビジネスロジック
│   │   ├── arxiv_service.py  # arXiv収集
│   │   ├── notion_service.py # Notion連携
│   │   └── translation.py    # 翻訳処理
│   └── utils/                # 共通ユーティリティ
│       └── helpers.py
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
```