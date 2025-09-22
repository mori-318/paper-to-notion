import customtkinter as ctk
from typing import List, Any, Dict
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

        # Notion保存チェックボックスの選択状態を管理する{paper_id: BooleanVar}
        self.save_notion_selected_vars: Dict[str, ctk.BooleanVar] = {}

        # UIコンポーネントを作成
        self._create_header()
        self._create_result_list()
        self._create_notion_save_button()

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

        # 水平配置用のメインフレーム
        content_frame = ctk.CTkFrame(item_frame)
        content_frame.pack(fill="x", expand=True, padx=4, pady=2)

        # 右側：Notion保存チェックボックス（先に右側を確保してから左を広げる）
        notion_frame = ctk.CTkFrame(content_frame, width=48)
        # 右側に固定幅のスペースを確保し、縦方向のみフィル
        notion_frame.pack(side="right", fill="y", padx=6, pady=6)
        # pack_propagate(False) でフレームの希望サイズを維持
        notion_frame.pack_propagate(False)

        # 左側：論文情報
        info_frame = ctk.CTkFrame(content_frame)
        info_frame.pack(side="left", fill="both", expand=True, padx=(10, 10), pady=6)

        # 論文属性を取得
        title = getattr(paper, "title", "(no title)")
        date = getattr(paper, "published_date", "")
        url = getattr(paper, "url", "")
        abstract_ja = getattr(paper, "abstract_ja", "")
        abstract_en = getattr(paper, "abstract", "")
        abstract = abstract_ja or abstract_en

        # タイトル（リンク風ラベル、折り返し対応）
        title_label = ctk.CTkLabel(
            info_frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
            fg_color="transparent",
            text_color="#1a5fb4",
            justify="left",
            wraplength=120,
        )
        title_label.pack(anchor="w", fill="x", padx=(12, 12), pady=(4, 2))
        # クリックでURLを開く
        if url:
            try:
                title_label.configure(cursor="hand2")
            except Exception:
                pass
            title_label.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))

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
                info_frame,
                text=meta_text,
                anchor="w",
                text_color="#008000"  # 緑
            )
            # 右側に余白を追加（内部余白を少し広めに）
            meta_label.pack(fill="x", padx=(12, 12))

        # アブストラクト（全文表示）
        abstract_label = ctk.CTkLabel(
            info_frame,
            text=abstract,
            anchor="w",
            justify="left",
            # 初期値は小さくして、後続の<Configure>で動的に更新
            wraplength=100
        )
        # 右側に余白を追加（内部余白を少し広めに）
        abstract_label.pack(fill="x", padx=(12, 12), pady=(2, 6))

        # フレームのサイズに合わせて折り返し幅を更新（スクロールバー幅分を差し引く）
        def _update_wraplength(event=None, lbl_abstract=abstract_label, lbl_title=title_label, frame=info_frame):
            try:
                w = frame.winfo_width()
                if w and w > 0:
                    # 右側のチェックボックス分と内部余白（左右 12px ずつ）を差し引く
                    wl = max(w - (24 + 24), 160)
                    lbl_abstract.configure(wraplength=wl)
                    lbl_title.configure(wraplength=wl)
            except Exception:
                pass

        info_frame.bind("<Configure>", _update_wraplength)

        # 選択状態管理用の変数
        var = ctk.BooleanVar(value=False)
        self.save_notion_selected_vars[paper.id] = var

        # チェックボックス
        checkbox = ctk.CTkCheckBox(
            notion_frame,
            text="",
            variable=var,
            width=20,
            height=20,
        )
        checkbox.pack(pady=10, padx=4)

    def _create_notion_save_button(self):
        """
        Notion保存ボタンを作成する
        ボタンを押すと、self.save_notion_selected_varsでチェックされた論文をNotionに保存する
        """
        self.notion_save_button = ctk.CTkButton(
            self,
            text="Notion DBに保存",
            command=self._save_to_notion,
        )
        self.notion_save_button.pack(pady=10)

    def _save_to_notion(self):
        """ 選択されたPaperをcontrollerに渡してNotionに保存する"""
        selected_papers = [
            paper for paper in self.papers
            if self.save_notion_selected_vars[paper.id].get()
        ]

        if not selected_papers:
            return

        # コントローラーに保存処理を依頼
        self.controller.save_to_notion(selected_papers)
