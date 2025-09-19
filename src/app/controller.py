from __future__ import annotations
from typing import Optional, Type, Callable, Union
import customtkinter as ctk
from domain.models import SearchConfig

# ビューは遅延インポートで使用（循環参照・起動時依存の回避）

class AppController:
    """
    アプリケーションの制御ロジックを管理するクラス
    - 画面遷移の制御
    - リクエスト送信/キャンセル
    """
    def __init__(self, window: ctk.CTk):
        # AppWindowのインスタンス (ルートウィンドウ)
        self.window = window
        # 実行中の非同期タスクがあれば管理 (将来拡張想定)
        self._is_cancelling = False

    def show_view(self, view: Union[Type[ctk.CTkFrame], Callable[[ctk.CTkFrame], ctk.CTkFrame]]):
        """
        指定ビューをメインコンテンツ領域に表示
        viewには以下のいずれかを渡せる:
            - CTkFrameのサブクラス (例：RequestView, LoadingView)
            - 親フレームを引数に取り、フレームを返す関数

        Args:
            view (Union[Type[ctk.CTkFrame], Callable[[ctk.CTkFrame], ctk.CTkFrame]]): 表示するビュー
        """
        content = getattr(self.window, "main_view").content_frame

        # 既存ウィジェットを破棄
        for widget in content.winfo_children():
            widget.destroy()

        # インスタンス生成（controller 付き/なしの両方に対応）
        instance: Optional[ctk.CTkFrame] = None
        try:
            # view が class or callable いずれでも、親フレームのみで一旦呼ぶ
            instance = view(content)  # type: ignore[arg-type]
        except TypeError:
            # controller を要求する場合はこちらで再試行
            try:
                instance = view(content, controller=self)  # type: ignore[misc]
            except TypeError as e:
                # それでもダメなら例外を再送出
                raise e

        assert instance is not None
        instance.pack(fill="both", expand=True)

    def submit_request(self, config: Optional[SearchConfig] = None):
        """
        検索リクエストを受け付けるハンドラ

        Args:
            config (Optional[SearchConfig]): 検索設定
        TODO: 現在は、ローディング画面へ遷移するのみ
        """
        # TODO: 検索実行ロジックの実装
        # 実行開始時は、キャンセルフラグを立てる
        from app.ui.views.loading_view import LoadingView  # 遅延インポート
        self._is_cancelling = False
        self.show_view(LoadingView)

    def cancel_request(self):
        """
        実行中の処理をキャンセルし、リクエスト入力画面へ戻す。
        """
        from app.ui.views.request_view import RequestView  # 遅延インポートで循環参照回避

        # 実際のキャンセル（ワーカー停止など）は今後の実装で対応
        self._is_cancelling = True
        self.show_view(RequestView)
