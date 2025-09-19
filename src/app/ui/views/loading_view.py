import customtkinter as ctk

class LoadingView(ctk.CTkFrame):
    """
    論文調査中のビュー
    """
    def __init__(self, master: ctk.CTkFrame, **kwargs):
        super().__init__(master, **kwargs)

        # ローディングメッセージ
        self.loading_label = ctk.CTkLabel(self, text="論文調査中...")
        self.loading_label.pack(pady=20)

        # プログレスバー
        self.progressbar = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progressbar.pack(pady=10)
        self.progressbar.start()