from turtle import color
import customtkinter as ctk
from typing import List, Any
import webbrowser
from datetime import datetime

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
        # 右側に余白を広めに取り、スクロールバーとの重なりを回避
        item_frame.pack(fill="x", padx=(5, 18), pady=6)

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
        # 右側に余白を追加
        title_button.pack(fill="x", padx=(2, 6))

        # メタ情報
        formatted_date = ""
        try:
            if date:
                ds = str(date)
                if ds.endswith("Z"):
                    ds = ds[:-1]
                dt = None
                try:
                    dt = datetime.fromisoformat(ds)
                except ValueError:
                    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
                        try:
                            dt = datetime.strptime(ds, fmt)
                            break
                        except ValueError:
                            continue
                if dt:
                    formatted_date = f"{dt.year}年{dt.month}月{dt.day}日"
        except Exception:
            formatted_date = str(date) if date else ""

        # 著者情報の取得と整形
        authors = getattr(paper, "authors", [])
        author_text = ""
        if authors:
            # 最大2名まで表示、3名以上は「et al.」を追加
            if len(authors) > 2:
                author_text = ", ".join(authors[:2]) + " et al."
            else:
                author_text = ", ".join(authors)

        # 日付と著者を結合（著者がいない場合は日付のみ）
        if formatted_date and author_text:
            meta_text = f"{formatted_date} || {author_text}"
        elif formatted_date:
            meta_text = formatted_date
        elif author_text:
            meta_text = author_text
        else:
            meta_text = ""

        if meta_text:
            meta_label = ctk.CTkLabel(
                item_frame,
                text=meta_text,
                anchor="w",
                text_color="#008000"  # 緑
            )
            # 右側に余白を追加
            meta_label.pack(fill="x", padx=(2, 6))

        # アブストラクト（全文表示）
        abstract_label = ctk.CTkLabel(
            item_frame,
            text=abstract,
            anchor="w",
            justify="left",
            # 初期値は小さくして、後続の<Configure>で動的に更新
            wraplength=100
        )
        # 右側に余白を追加
        abstract_label.pack(fill="x", padx=(2, 6))

        # フレームのサイズに合わせて折り返し幅を更新（スクロールバー幅分を差し引く）
        def _update_wraplength(event=None, lbl=abstract_label, frame=item_frame):
            try:
                w = frame.winfo_width()
                if w and w > 0:
                    lbl.configure(wraplength=max(w - 10, 120))
            except Exception:
                pass

        item_frame.bind("<Configure>", _update_wraplength)
