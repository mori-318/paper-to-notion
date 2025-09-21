from __future__ import annotations
from typing import Optional, List, Callable
from dataclasses import dataclass
from google import genai
from dotenv import load_dotenv
import os
import logging


@dataclass
class TranslationConfig:
    """翻訳モデル設定"""
    model: str = "gemini-1.5-flash"
    system_prompt: str = "以下の英文を日本語に翻訳し、100字以内に要約した結果のみを出力してください。"
    temperature: float = 1.0
    max_tokens: int = 512


class TranslationService:
    """
    ローカルLMを使った翻訳サービス
    """

    def __init__(self, cfg: Optional[TranslationConfig] = None):
        self.cfg = cfg or TranslationConfig()
        # .env から GEMINI_API_KEY を読み込み
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            logging.error("GEMINI_API_KEY が .env に設定されていません")
            raise ValueError("GEMINI_API_KEY is not set in .env")

        # Google GenAI クライアントを初期化
        self.client = genai.Client(api_key=api_key)
        logging.info(f"モデルの読み込み完了: {self.cfg.model}")
        self._is_cancelled = False
        self._is_cancelled_getter = None

    def set_cancel_flag(self, flag_getter: Callable[[], bool]):
        """
        キャンセル状態を取得する関数を設定
        Args:
            flag_getter: キャンセル状態を返す関数
        """
        self._is_cancelled_getter = flag_getter

    def translate_en_to_jp(self, texts: List[str]) -> List[str]:
        """
        英文を日本語に翻訳する
        Args:
            texts (List[str]): 翻訳したい英文リスト
        Returns:
            List[str]: 翻訳した日本語リスト
        """

        logging.info(f"翻訳開始: {len(texts)}件")

        # 指示文は contents に前置して渡す（models.generate_content には system_instruction 引数が無い）
        instruction = self.cfg.system_prompt

        translated_texts = []
        for text in texts:
            # キャンセルチェック
            if self._is_cancelled_getter and self._is_cancelled_getter():
                logging.info("翻訳処理がキャンセルされました")
                raise TranslationCanceledException("翻訳がユーザーによりキャンセルされました")

            # 空文字の場合は、空文字を返す
            if not text:
                translated_texts.append("")
                continue

            # 進捗ログ
            logging.info(f"翻訳中: {text[:20]}...")

            try:
                # Gemini へ送信（google-genai 最新API）
                res = self.client.models.generate_content(
                    model=self.cfg.model,
                    contents=[
                        {
                            "role": "user",
                            "parts": [
                                {"text": f"{instruction}\n\n{text}"}
                            ]
                        }
                    ]
                )
                # レスポンステキストを安全に抽出
                out_text = getattr(res, "text", None)
                if not out_text:
                    out_text = getattr(res, "output_text", "") or ""
                logging.info(f"翻訳完了: {out_text[:20]}...")
                translated_texts.append(out_text)
            except Exception as e:
                logging.exception("翻訳失敗: %s", e)
                translated_texts.append("")

        # Google GenAI クライアントは明示的な close 不要
        self.client = None

        return translated_texts


class TranslationCanceledException(Exception):
    """翻訳がキャンセルされたことを示す例外"""
    pass
