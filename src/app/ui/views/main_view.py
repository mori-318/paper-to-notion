import customtkinter as ctk

class MainView(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, **kwargs):
        super().__init__(master, **kwargs)

        # 画面タイトル
        self.title_label = ctk.CTkLabel(self, text="論文調査ツール", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=20)

        # コンテンツフレーム（ここに各画面を表示）
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def show_view(self, view: ctk.CTkFrame):
        """
        指定したビューを表示

        Args:
            view (ctk.CTkFrame): 表示するビュー
        """
        # 既存のコンテンツをクリア
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # 新しいビューを表示
        view(self.content_frame).pack(fill="both", expand=True)