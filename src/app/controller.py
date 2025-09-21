from __future__ import annotations
from typing import Optional, Type, Callable, Union, List
import threading
import customtkinter as ctk
import logging

from domain.models import SearchConfig, Paper
from services.arxiv_service import ArxivService
from services.notion_service import NotionService
from services.translation_service import TranslationService, TranslationCanceledException
from app.ui.views.result_view import ResultView
from app.ui.views.loading_view import LoadingView


class AppController:
    """
    アプリケーションの制御ロジックを管理するクラス
    - 画面遷移の制御
    - リクエスト送信/キャンセル
    - arXiv検索
    - 翻訳
    - Notion保存
    """
    def __init__(self, window: ctk.CTk):
        # AppWindowのインスタンス (ルートウィンドウ)
        self.window = window
        # 実行中の非同期タスクがあれば管理 (将来拡張想定)
        self._is_cancelling = False
        # Notion サービス（必要時に初期化）
        self.notion_service: Optional[NotionService] = None
        # 直近の検索結果（ResultView 再表示時に使用）
        self._last_papers: List[Paper] = []

    def show_view(
        self,
        view: Union[
            Type[ctk.CTkFrame],
            Callable[[ctk.CTkFrame], ctk.CTkFrame],
        ],
        message: Optional[str] = None,
    ):
        """
        指定ビューをメインコンテンツ領域に表示
        viewには以下のいずれかを渡せる:
            - CTkFrameのサブクラス (例：RequestView, LoadingView)
            - 親フレームを引数に取り、フレームを返す関数

        Args:
            view (Union[Type[ctk.CTkFrame], Callable[[ctk.CTkFrame], ctk.CTkFrame]]): 表示するビュー
            message (Optional[str]): 表示するメッセージ
        """
        content = getattr(self.window, "main_view").content_frame

        # 既存ウィジェットを破棄
        for widget in content.winfo_children():
            widget.destroy()

        # インスタンス生成（クラス or ファクトリ関数で分岐）
        instance: Optional[ctk.CTkFrame] = None
        if isinstance(view, type) and issubclass(view, ctk.CTkFrame):
            # ビュークラスなら controller を渡して初期化を試みる
            try:
                instance = view(content, controller=self)  # type: ignore[misc]
            except TypeError:
                instance = view(content)  # type: ignore[arg-type]
        else:
            # ファクトリ（callable）は親のみ渡す
            instance = view(content)  # type: ignore[arg-type]

        assert instance is not None
        # LoadingView などメッセージ更新対応ビューなら反映
        if message and hasattr(instance, "update_message"):
            try:
                instance.update_message(message)  # type: ignore[attr-defined]
            except Exception:
                pass
        instance.pack(fill="both", expand=True)

    def submit_request(self, config: Optional[SearchConfig] = None):
        """
        検索リクエストを受け付けるハンドラ

        Args:
            config (Optional[SearchConfig]): 検索設定
        """
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
                translator.set_cancel_flag(lambda: self._is_cancelling)

                # 全てのabstractをリストにまとめて翻訳
                abstracts = [p.abstract for p in papers]
                translated_abstracts = translator.translate_en_to_jp(abstracts)

                # 翻訳結果を元の論文オブジェクトに設定
                for paper, translated_abstract in zip(papers, translated_abstracts):
                    paper.abstract_ja = translated_abstract

            except Exception as e:
                # キャンセル例外は特別扱い
                if isinstance(e, TranslationCanceledException):
                    logging.info("翻訳がキャンセルされました")
                    return
                else:
                    # その他の例外はログに残す
                    logging.exception("翻訳処理で例外が発生しました")

        except Exception as e:
            # エラー時はエラービューを表示
            error_msg = f"検索中にエラーが発生しました: {e}"

            def error_view(parent: ctk.CTkFrame) -> ctk.CTkFrame:
                frame = ctk.CTkFrame(parent)
                ctk.CTkLabel(frame, text=error_msg).pack(pady=20)
                ctk.CTkButton(
                    frame,
                    text="戻る",
                    command=self.cancel_request,
                ).pack(pady=10)
                return frame
            self.window.after(0, lambda: self.show_view(error_view))
            return

        if self._is_cancelling:
            return

        # 検索結果を保持し、メインスレッドで結果表示
        self._last_papers = papers
        self.window.after(
            0,
            lambda: self.show_view(
                lambda parent: ResultView(
                    parent,
                    controller=self,
                    papers=self._last_papers,
                )
            ),
        )

    def cancel_request(self):
        """
        実行中の処理をキャンセルし、リクエスト入力画面へ戻す。
        """
        from app.ui.views.request_view import RequestView  # 遅延インポートで循環参照回避

        # 実際のキャンセル（ワーカー停止など）は今後の実装で対応
        self._is_cancelling = True
        self.show_view(RequestView)

    def save_to_notion(self, papers: List[Paper]):
        """
        Notionに論文を保存する
        Args:
            papers (List[Paper]): 保存する論文オブジェクトのリスト
        """
        if not papers:
            self._show_error("保存する論文がありません")
            return

        # ローディング表示
        self.show_view(LoadingView, message="Notion保存中...")

        # 非同期で保存処理
        threading.Thread(
            target=self._save_to_notion_thread,
            args=(papers,),
            daemon=True,  # デーモンスレッドとして設定
        ).start()

    def _save_to_notion_thread(self, papers: List[Paper]):
        """
        バックグラウンドで論文をNotionに保存する
        Args:
            papers (List[Paper]): 保存する論文オブジェクトのリスト
        """
        try:
            # NotionService の遅延初期化
            if self.notion_service is None:
                try:
                    self.notion_service = NotionService()
                except Exception:
                    # 初期化失敗（環境変数未設定など）
                    self.window.after(0, lambda: self._show_error("Notionの設定が未完了です。環境変数を確認してください。"))
                    return
            success_ids = []
            for paper in papers:
                if self._is_cancelling:
                    break
                ok = self.notion_service.create_page(paper)
                if ok:
                    success_ids.append(paper.id)
        except Exception:
            logging.exception("Notion保存中に例外が発生しました")
            self.window.after(0, lambda: self._show_error("Notion保存中にエラーが発生しました"))
        finally:
            # 成功した論文を一覧から除外
            def _finish():
                if isinstance(success_ids, list) and success_ids:
                    self._last_papers = [p for p in self._last_papers if p.id not in success_ids]
                # 更新後の一覧を表示
                self.show_view(
                    lambda parent: ResultView(
                        parent,
                        controller=self,
                        papers=self._last_papers,
                    )
                )
            self.window.after(0, _finish)

    def _show_error(self, message: str):
        """簡易的なエラービューを表示"""
        def error_view(parent: ctk.CTkFrame) -> ctk.CTkFrame:
            frame = ctk.CTkFrame(parent)
            ctk.CTkLabel(frame, text=message).pack(pady=20)
            ctk.CTkButton(
                frame,
                text="戻る",
                command=lambda: self.show_view(
                    lambda p: ResultView(
                        p,
                        controller=self,
                        papers=self._last_papers,
                    )
                ),
            ).pack(pady=10)
            return frame
        self.show_view(error_view)
