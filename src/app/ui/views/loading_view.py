import customtkinter as ctk


class LoadingView(ctk.CTkFrame):
    """
    非同期処理（論文検索、Notion保存など）の実行中に表示するビュー。

    プログレスバーとキャンセルボタンを持つ。
    """
    def __init__(self, master: ctk.CTkFrame, controller=None, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller

        # ローディングメッセージ
        self.loading_label = ctk.CTkLabel(self, text="論文調査中...")
        self.loading_label.pack(pady=20)

        # プログレスバー
        self.progressbar = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progressbar.pack(pady=10)
        self.progressbar.start()

        # キャンセルボタン（controller があれば有効化）
        self.cancel_button = ctk.CTkButton(
            self,
            text="キャンセル",
            command=(self.controller.cancel_request if self.controller else None),
        )
        # controller が無い場合は無効化
        if self.controller is None:
            self.cancel_button.configure(state="disabled")
        self.cancel_button.pack(pady=10)

    def update_message(self, message: str):
        """ローディングメッセージを更新する。"""
        try:
            self.loading_label.configure(text=message)
        except Exception:
            pass
