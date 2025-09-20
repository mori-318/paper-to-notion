import customtkinter as ctk
from typing import List, Any
import webbrowser

class ResultView(ctk.CTkFrame):
    """
    検索結果を表示するビュー
    Args:
        master (ctk.CTkFrame): 親フレーム
        controller: 画面遷移用コントローラ（戻るボタン等で使用）
        papers (List[object]): 検索結果の論文リスト
    """
    def __init__(self, master: ctk.CTkFrame, controller=None, papers: List[Any] | None = None, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.papers = papers or []

        # UIコンポーネントを作成
        self._create_header()
        self._create_result_list()

    def _create_header(self):
        """ヘッダー部分を作成"""
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.pack(fill="x", padx=10, pady=10)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="検索結果",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.title_label.pack(side="left")

        if self.controller:
            self.back_button = ctk.CTkButton(
                self.header_frame,
                text="条件へ戻る",
                command=self.controller.cancel_request
            )
            self.back_button.pack(side="right")
        else:
            self.back_button = ctk.CTkButton(self.header_frame, text="条件へ戻る")
            self.back_button.configure(state="disabled")
            self.back_button.pack(side="right")

    def _create_result_list(self):
        """結果リスト部分を作成"""
        self.list_frame = ctk.CTkScrollableFrame(self, height=400)
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        if not self.papers:
            no_results_label = ctk.CTkLabel(
                self.list_frame,
                text="該当する論文が見つかりませんでした。"
            )
            no_results_label.pack(pady=20)
            return

        for paper in self.papers:
            self._create_paper_item(paper)

    def _create_paper_item(self, paper):
        """個々の論文アイテムを作成"""
        item_frame = ctk.CTkFrame(self.list_frame)
        item_frame.pack(fill="x", padx=5, pady=6)

        # 論文属性を取得
        title = getattr(paper, "title", "(no title)")
        date = getattr(paper, "published_date", "")
        url = getattr(paper, "url", "")
        abstract_ja = getattr(paper, "abstract_ja", "")
        abstract_en = getattr(paper, "abstract", "")
        abstract = abstract_ja or abstract_en

        # タイトルリンク
        title_button = ctk.CTkButton(
            item_frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
            fg_color="transparent",
            hover_color="#f0f0f0",
            text_color="#1a5fb4",
            command=lambda u=url: webbrowser.open(u) if u else None
        )
        title_button.pack(fill="x")

        # メタ情報
        meta_label = ctk.CTkLabel(
            item_frame,
            text=f"{date}  |  {url}",
            anchor="w"
        )
        meta_label.pack(fill="x")

        # アブストラクトプレビュー
        preview = abstract[:200] + ("..." if len(abstract) > 200 else "")
        abstract_label = ctk.CTkLabel(
            item_frame,
            text=preview,
            anchor="w",
            justify="left",
            wraplength=800
        )
        abstract_label.pack(fill="x")
