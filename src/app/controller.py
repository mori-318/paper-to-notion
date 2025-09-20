from __future__ import annotations
from typing import Optional, Type, Callable, Union, List
import threading
import customtkinter as ctk
import logging

from domain.models import SearchConfig
from services.arxiv_service import ArxivService
from services.translation_service import TranslationService
from app.ui.views.result_view import ResultView

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
            # まず controller を渡して試す（渡しても受理できるクラスでは有効にするため）
            instance = view(content, controller=self)  # type: ignore[misc]
        except TypeError:
            # controller を受け付けないコンストラクタの場合はフォールバック
            try:
                instance = view(content)  # type: ignore[arg-type]
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
        """
        from app.ui.views.loading_view import LoadingView  # 遅延インポート
        self._is_cancelling = False
        # ローディング表示
        self.show_view(LoadingView)

        if config is None:
            return

        # バックグラウンドで検索を実行
        t = threading.Thread(target=self._run_search, args=(config,), daemon=True)
        t.start()

    def _run_search(self, config: SearchConfig):
        """
        別スレッドで arXiv 検索を実行し、完了後に結果ビューを表示する。
        Args:
            config (SearchConfig): 検索設定
        """
        # サービス呼び出し
        try:
            service = ArxivService()
            papers = service.search_papers(
                keywords=config.keyword,
                max_results=config.max_results,
                start_date=config.start_date,
                end_date=config.end_date,
            )

            logging.info(f"検索結果: {len(papers)}件")
            # 翻訳（バッチ処理）
            try:
                translator = TranslationService()

                # 全てのabstractをリストにまとめて翻訳
                abstracts = [p.abstract for p in papers]
                translated_abstracts = translator.translate_en_to_jp(abstracts)

                # 翻訳結果を元の論文オブジェクトに設定
                for paper, translated_abstract in zip(papers, translated_abstracts):
                    paper.abstract_ja = translated_abstract

            except Exception as e:
                # 翻訳が失敗しても検索結果は表示するが、原因はログに残す
                logging.exception("翻訳処理で例外が発生しました")

        except Exception as e:
            # エラー時はエラービューを表示
            def error_view(parent: ctk.CTkFrame) -> ctk.CTkFrame:
                frame = ctk.CTkFrame(parent)
                ctk.CTkLabel(frame, text=f"検索中にエラーが発生しました: {e}").pack(pady=20)
                ctk.CTkButton(frame, text="戻る", command=self.cancel_request).pack(pady=10)
                return frame
            self.window.after(0, lambda: self.show_view(error_view))
            return

        if self._is_cancelling:
            return

        # メインスレッドで結果表示 (論文ごとにResultViewを作成して表示する)
        self.window.after(0, lambda: self.show_view(lambda parent: ResultView(parent, controller=self, papers=papers)))

    def cancel_request(self):
        """
        実行中の処理をキャンセルし、リクエスト入力画面へ戻す。
        """
        from app.ui.views.request_view import RequestView  # 遅延インポートで循環参照回避

        # 実際のキャンセル（ワーカー停止など）は今後の実装で対応
        self._is_cancelling = True
        self.show_view(RequestView)
