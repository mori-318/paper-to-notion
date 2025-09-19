import customtkinter as ctk

from ui.views.main_view import MainView
from ui.views.loading_view import LoadingView

class AppWindow(ctk.CTk):
    """
    アプリケーションウィンドウ
    """
    def __init__(self):
        super().__init__()
        self.title("論文調査ツール")
        self.geometry("800x600")
        self.resizable(False, False)

        # メインビューを表示
        self.main_view = MainView(self)
        self.main_view.pack(fill="both", expand=True)

        # 初期画面として、ローディングビューを表示
        self.main_view.show_view(LoadingView)
