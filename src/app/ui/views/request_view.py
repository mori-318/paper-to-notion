import os
import json
from datetime import date, timedelta, datetime
import customtkinter as ctk
from domain.models import SearchConfig
from tkcalendar import DateEntry


class RequestView(ctk.CTkFrame):
    """
    論文調査条件を入力するフォームビュー
    """
    def __init__(self, master: ctk.CTkFrame, controller):
        super().__init__(master)
        self.controller = controller
        # 保存先パスを用意(アプリ専用フォルダを~に用意し、keywords.jsonを保存する)
        self._store_path = os.path.join("src", "config", "keywords.json")
        self._saved_keywords = self._load_saved_keywords()

        # キーワード入力フィールド
        self.keyword_frame = ctk.CTkFrame(self)
        self.keyword_frame.pack(pady=10, fill="x")
        ctk.CTkLabel(self.keyword_frame, text="キーワード:").pack(side="left", padx=5)
        self.keyword_entry = ctk.CTkEntry(
            self.keyword_frame,
            placeholder_text="キーワードを入力...",
            width=300,
        )
        self.keyword_entry.pack(side="left", padx=5)

        # 保存済みキーワードの選択UI
        self.saved_frame = ctk.CTkFrame(self)
        self.saved_frame.pack(pady=4, fill="x")
        ctk.CTkLabel(self.saved_frame, text="保存済みキーワード:").pack(side="left", padx=5)
        values = self._saved_keywords if self._saved_keywords else ["(なし)"]
        self.saved_var = ctk.StringVar(value=values[0])
        self.saved_menu = ctk.CTkOptionMenu(
            self.saved_frame,
            variable=self.saved_var,
            values=values,
            command=self._on_select_saved,
        )
        self.saved_menu.pack(side="left", padx=5)

        # キーワード保存チェックボックス
        self.save_keyword_var = ctk.BooleanVar(value=False)
        self.save_keyword_checkbox = ctk.CTkCheckBox(
            self.keyword_frame,
            text="キーワードを保存",
            variable=self.save_keyword_var,
        )
        self.save_keyword_checkbox.pack(side="left", padx=5)

        # 調査数設定
        self.max_results_frame = ctk.CTkFrame(self)
        self.max_results_frame.pack(pady=10, fill="x")
        ctk.CTkLabel(
            self.max_results_frame,
            text="調査数:",
        ).pack(side="left", padx=5)

        # 調査数スライダ-
        self.max_results_slider = ctk.CTkSlider(
            self.max_results_frame,
            from_=1,
            to=50,
            number_of_steps=49,
            width=200,
        )
        self.max_results_slider.set(5)
        self.max_results_slider.pack(side="left", padx=5)

        # 調査数テキスト入力
        self.max_results_entry = ctk.CTkEntry(
            self.max_results_frame,
            width=50,
        )
        self.max_results_entry.insert(0, "5")
        self.max_results_entry.pack(side="left", padx=5)

        # スライダーとテキストボックスの連動
        self.max_results_slider.configure(command=self._update_max_results_entry)
        self.max_results_entry.bind("<Return>", self._update_max_results_slider)

        # 日付範囲（開始/終了をカレンダーから選択）
        self.date_range_frame = ctk.CTkFrame(self)
        self.date_range_frame.pack(pady=10, fill="x")
        # カレンダーの視認性を上げるためのスタイル指定
        calendar_style = {
            "font": ("Helvetica", 16),
            "foreground": "#ffffff",
            "background": "#2b2b2b",
            "headersforeground": "#ffffff",
            "headersbackground": "#3a3a3a",
            "normalforeground": "#ffffff",
            "normalbackground": "#2b2b2b",
            "weekendforeground": "#ffd166",
            "weekendbackground": "#2b2b2b",
            "othermonthforeground": "#9aa0a6",
            "othermonthbackground": "#2b2b2b",
            "selectbackground": "#1f6aa5",
            "selectforeground": "#ffffff",
        }
        ctk.CTkLabel(self.date_range_frame, text="開始日:").pack(side="left", padx=5)
        self.start_date_entry = DateEntry(self.date_range_frame, date_pattern="yyyy-mm-dd", width=10, **calendar_style)
        self.start_date_entry.pack(side="left", padx=(0, 4))
        # 開始日 無期限チェック
        self.start_infinite_var = ctk.BooleanVar(value=False)
        self.start_infinite_checkbox = ctk.CTkCheckBox(
            self.date_range_frame,
            text="無期限",
            variable=self.start_infinite_var,
            command=self._on_toggle_start_infinite,
        )
        self.start_infinite_checkbox.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(self.date_range_frame, text="終了日:").pack(side="left", padx=5)
        self.end_date_entry = DateEntry(self.date_range_frame, date_pattern="yyyy-mm-dd", width=10, **calendar_style)
        self.end_date_entry.pack(side="left", padx=(0, 4))
        # 終了日 無期限チェック
        self.end_infinite_var = ctk.BooleanVar(value=False)
        self.end_infinite_checkbox = ctk.CTkCheckBox(
            self.date_range_frame,
            text="無期限",
            variable=self.end_infinite_var,
            command=self._on_toggle_end_infinite,
        )
        self.end_infinite_checkbox.pack(side="left")

        # デフォルト値: 開始=今日-30日, 終了=今日
        _today = date.today()
        _start_default = _today - timedelta(days=30)
        try:
            self.start_date_entry.set_date(_start_default)
            self.end_date_entry.set_date(_today)
        except Exception:
            pass

        # 無期限チェック時の初期状態反映（デフォルトはオフなので何もしない）

        # 送信ボタン
        self.submit_button = ctk.CTkButton(
            self,
            text="調査開始",
            command=self.submit_request,
        )
        self.submit_button.pack(pady=10)

    def _update_max_results_entry(self, value):
        """
        スライダーの値をテキストボックスに反映
        """
        self.max_results_entry.delete(0, "end")
        self.max_results_entry.insert(0, str(int(value)))

    def _update_max_results_slider(self, event):
        """
        テキストボックスでEnterが押されたときにスライダーを更新
        """
        try:
            value = int(self.max_results_entry.get())
            if 1 <= value <= 50:
                self.max_results_slider.set(value)
        except ValueError:
            pass

    def _ensure_store_dir(self):
        """保存先ディレクトリを確保"""
        os.makedirs(os.path.dirname(self._store_path), exist_ok=True)

    def _load_saved_keywords(self) -> list[str]:
        """保存済みキーワードを読み込む"""
        try:
            if not os.path.exists(self._store_path):
                return []
            with open(self._store_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            items = data.get("keywords", [])
            return [str(x) for x in items if isinstance(x, str) and x.strip()]
        except Exception:
            return []

    def _save_keyword(self, kw: str):
        """
        キーワードを保存（重複は先頭に移動、最大10件）
        Args:
            kw(str): 保存するキーワード
        """
        kw = (kw or "").strip()
        if not kw:
            return
        items = list(self._saved_keywords)
        if kw in items:
            items.remove(kw)
        items.insert(0, kw)
        if len(items) > 10:
            items = items[:10]

        self._ensure_store_dir()
        try:
            with open(self._store_path, "w", encoding="utf-8") as f:
                json.dump({"keywords": items}, f, ensure_ascii=False, indent=2)
            self._saved_keywords = items
            self._update_saved_keywords_menu()
        except Exception:
            pass

    def _update_saved_keywords_menu(self):
        """保存済みキーワードの選択UIを更新"""
        values = self._saved_keywords if self._saved_keywords else ["(なし)"]
        self.saved_menu.configure(values=values)
        if self._saved_keywords:
            self.saved_var.set(self._saved_keywords[0])
        else:
            self.saved_var.set("(なし)")

    def _on_select_saved(self, choice: str):
        """
        保存済みキーワードを選択したときにキーワード入力欄を更新
        Args:
            choice(str): 選択されたキーワード
        """
        if choice and choice != "(なし)":
            self.keyword_entry.delete(0, "end")
            self.keyword_entry.insert(0, choice)

    def submit_request(self):
        """
        リクエストを送信
        """
        # 無期限チェックの状態に応じて処理
        start_infinite = self.start_infinite_var.get()
        end_infinite = self.end_infinite_var.get()

        if start_infinite:
            start_date = ""  # 無期限（下限なし）
        else:
            start_dt = self.start_date_entry.get_date()
            start_date = self._to_relative_jp(start_dt)

        if end_infinite:
            end_date = ""  # 無期限（上限なし）
        else:
            end_dt = self.end_date_entry.get_date()
            end_date = self._to_relative_jp(end_dt)

        # 両方とも有効日付のときのみ前後関係を正す（空文字は無期限）
        if start_date and end_date:
            start_dt2 = self.start_date_entry.get_date()
            end_dt2 = self.end_date_entry.get_date()
            if end_dt2 < start_dt2:
                # スワップして再計算
                start_date, end_date = end_date, start_date

        config = SearchConfig(
            keyword=[self.keyword_entry.get()],
            max_results=int(self.max_results_entry.get()),
            start_date=start_date,
            end_date=end_date,
        )

        # キーワード保存チェックが入っていいる場合、設定を保存
        if self.save_keyword_var.get():
            self._save_keyword(self.keyword_entry.get())

        # コントローラーに設定を渡す
        self.controller.submit_request(config)

    def _on_toggle_start_infinite(self):
        """開始日 無期限のON/OFFでDateEntryを有効/無効化"""
        try:
            if self.start_infinite_var.get():
                self.start_date_entry.configure(state="disabled")
            else:
                self.start_date_entry.configure(state="normal")
        except Exception:
            pass

    def _on_toggle_end_infinite(self):
        """終了日 無期限のON/OFFでDateEntryを有効/無効化"""
        try:
            if self.end_infinite_var.get():
                self.end_date_entry.configure(state="disabled")
            else:
                self.end_date_entry.configure(state="normal")
        except Exception:
            pass

    def _text_to_relative_jp(self, s: str) -> str | None:
        """
        ユーザー入力文字列を相対表現（X年Y月Z日前）に変換して返す。
        サポート:
        - 絶対日付: YYYY-MM-DD / YYYY/MM/DD / YYYY.MM.DD
        - 相対表現: 「X年Y月Z日前」または「X年前」「Yヶ月前」「Z日前」等の部分指定
        - キーワード: 今日 / yesterday(昨日) / today
        - 簡易相対: -30d, -1m, -1y
        変換できない場合は None を返す。
        """
        import re
        s = (s or "").strip()
        if not s:
            return None
        # today / 今日
        if s in ("今日", "today"):
            return "0年0月0日前"
        if s in ("昨日", "yesterday"):
            return "0年0月1日前"
        # -Nd / -Nm / -Ny
        m = re.fullmatch(r"-?\s*(\d+)\s*([dmyDMY])", s)
        if m:
            n = int(m.group(1))
            unit = m.group(2).lower()
            if unit == "d":
                return f"0年0月{n}日前"
            if unit == "m":
                return f"0年{n}月0日前"
            if unit == "y":
                return f"{n}年0月0日前"
        # 既に相対表現（完全形）
        if re.fullmatch(r"\d+年\d+月\d+日前", s):
            return s
        # 部分指定（例: 1年前, 3ヶ月前, 10日前）を統合
        y = mth = d = 0
        for pat, attr in ((r"(\d+)年\s*前", "y"), (r"(\d+)ヶ月\s*前", "m"), (r"(\d+)月\s*前", "m"), (r"(\d+)日\s*前", "d")):
            m2 = re.search(pat, s)
            if m2:
                val = int(m2.group(1))
                if attr == "y":
                    y = val
                elif attr == "m":
                    mth = val
                else:
                    d = val
        if y or mth or d:
            return f"{y}年{mth}月{d}日前"
        # 絶対日付
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
            try:
                dt = datetime.strptime(s, fmt).date()
                return self._to_relative_jp(dt)
            except Exception:
                pass
        return None

    def _to_relative_jp(self, target: date) -> str:
        """絶対日付を「X年Y月Z日前」に変換（365日=1年, 30日=1ヶ月の簡易換算）"""
        today = date.today()
        delta_days = (today - target).days
        if delta_days < 0:
            delta_days = 0
        y = delta_days // 365
        rem = delta_days % 365
        m = rem // 30
        d = rem % 30
        return f"{y}年{m}月{d}日前"
