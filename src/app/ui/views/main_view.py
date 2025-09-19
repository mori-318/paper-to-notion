import customtkinter as ctk

class MainView(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, **kwargs):
        super().__init__(master, **kwargs)

        # 画面タイトル
        self.title_label = ctk.CTkLabel(self, text="Paper to Notion", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=20)

        # コンテンツフレーム（ここに各画面を表示）
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)