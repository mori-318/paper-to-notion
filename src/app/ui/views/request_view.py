import customtkinter as ctk
from domain.models import SearchConfig

class RequestView(ctk.CTkFrame):
    """
    論文調査条件を入力するフォームビュー
    """
    def __init__(self, master: ctk.CTkFrame, controller):
        super().__init__(master)
        self.controller = controller

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

        self.max_results_slider = ctk.CTkSlider(
            self.max_results_frame,
            from_=1,
            to=50,
            number_of_steps=49,
            width=200,
        )
        self.max_results_slider.set(5)
        self.max_results_slider.pack(side="left", padx=5)

        self.max_results_entry = ctk.CTkEntry(
            self.max_results_frame,
            width=50,
        )
        self.max_results_entry.insert(0, "5")
        self.max_results_entry.pack(side="left", padx=5)

        # スライダーとテキストボックスの連動
        self.max_results_slider.configure(command=self._update_max_results_entry)
        self.max_results_entry.bind("<Return>", self._update_max_results_slider)

        # 日付範囲（[]年[]月[]日前 ~ []年[]月[]日前まで）
        self.date_range_frame = ctk.CTkFrame(self)
        self.date_range_frame.pack(pady=10, fill="x")
        ctk.CTkLabel(self.date_range_frame, text="日付範囲:").pack(side="left", padx=5)

        # 開始: []年 []月 []日前
        self.start_year_var = ctk.StringVar(value="0")
        self.start_month_var = ctk.StringVar(value="1")
        self.start_day_var = ctk.StringVar(value="0")

        self.start_year_entry = ctk.CTkEntry(self.date_range_frame, width=40, textvariable=self.start_year_var)
        self.start_year_entry.pack(side="left")
        ctk.CTkLabel(self.date_range_frame, text="年").pack(side="left", padx=(2, 6))
        self.start_month_entry = ctk.CTkEntry(self.date_range_frame, width=40, textvariable=self.start_month_var)
        self.start_month_entry.pack(side="left")
        ctk.CTkLabel(self.date_range_frame, text="ヶ月").pack(side="left", padx=(2, 6))
        self.start_day_entry = ctk.CTkEntry(self.date_range_frame, width=40, textvariable=self.start_day_var)
        self.start_day_entry.pack(side="left")
        ctk.CTkLabel(self.date_range_frame, text="日前").pack(side="left", padx=(2, 10))

        # チルダ
        ctk.CTkLabel(self.date_range_frame, text="~").pack(side="left", padx=6)

        # 終了: []年 []月 []日前 まで
        self.end_year_var = ctk.StringVar(value="0")
        self.end_month_var = ctk.StringVar(value="0")
        self.end_day_var = ctk.StringVar(value="0")

        self.end_year_entry = ctk.CTkEntry(self.date_range_frame, width=40, textvariable=self.end_year_var)
        self.end_year_entry.pack(side="left")
        ctk.CTkLabel(self.date_range_frame, text="年").pack(side="left", padx=(2, 6))
        self.end_month_entry = ctk.CTkEntry(self.date_range_frame, width=40, textvariable=self.end_month_var)
        self.end_month_entry.pack(side="left")
        ctk.CTkLabel(self.date_range_frame, text="ヶ月").pack(side="left", padx=(2, 6))
        self.end_day_entry = ctk.CTkEntry(self.date_range_frame, width=40, textvariable=self.end_day_var)
        self.end_day_entry.pack(side="left")
        ctk.CTkLabel(self.date_range_frame, text="日前まで").pack(side="left", padx=(2, 0))

        # 送信ボタン
        self.submit_button = ctk.CTkButton(
            self,
            text="調査開始",
            command=self._submit_request,
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

    def submit_request(self):
        """
        リクエストを送信
        """
        # フォームデータを収集
        # 週は0固定で内部フォーマットを構築
        start_date = f"{self.start_year_var.get()}年{self.start_month_var.get()}月{self.start_day_var.get()}日前"
        end_date = f"{self.end_year_var.get()}年{self.end_month_var.get()}月{self.end_day_var.get()}日前"

        config = SearchConfig(
            keyword=[self.keyword_entry.get()],
            max_results=int(self.max_results_entry.get()),
            start_date=start_date,
            end_date=end_date,
        )

        # キーワード保存チェックが入っている場合、設定を保存
        if self.save_keyword_var.get():
            # TODO: キーワード保存処理を後で実装
            pass

        # コントローラーに設定を渡す
        self.controller.submit_request(config)