import customtkinter as ctk
from app.ui.views.main_view import MainView
from app.ui.views.request_view import RequestView
from .controller import AppController


class AppWindow(ctk.CTk):
    """
    アプリケーションのメインウィンドウ。

    UI全体のコンテナとして機能する。
    """
    def __init__(self):
        super().__init__()
        self.title("論文調査ツール")
        self.geometry("600x700")
        self.resizable(False, False)

        # コントローラーの作成
        self.controller = AppController(self)

        # メインビューを表示
        self.main_view = MainView(
            master=self,
        )
        self.main_view.pack(fill="both", expand=True)

        # 初期画面として、リクエストビューを表示
        self.controller.show_view(RequestView)
