from __future__ import annotations
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from openai import OpenAI
import logging

@dataclass
class TranslationConfig:
    """翻訳モデル設定"""
    model: str = "7shi/gemma-2-jpn-translate:2b-instruct-q8_0"
    system_prompt: str = "以下の英文を日本語に翻訳し、翻訳した結果のみを出力してください。 例：(入力)This is a test. -> (出力)これはテストです。"
    temperature: float = 1.0
    max_tokens: int = 2048
    base_url: str = "http://localhost:11434/v1"
    api_key: str = "ollama"


class TranslationService:
    """
    ローカルLMを使った翻訳サービス
    """

    def __init__(self, cfg: Optional[TranslationConfig] = None):
        self.cfg = cfg or TranslationConfig()
        # 直接クライアントを保持して簡潔化
        self.client = OpenAI(
            base_url=self.cfg.base_url,
            api_key=self.cfg.api_key
        )
        logging.info(f"モデルの読み込み完了: {self.cfg.model}")

    def translate_en_to_jp(self, texts: List[str]) -> List[str]:
        """
        英文を日本語に翻訳する
        Args:
            texts (List[str]): 翻訳したい英文リスト
        Returns:
            List[str]: 翻訳した日本語リスト
        """

        logging.info(f"翻訳開始: {texts}")

        # このモデルは system ロール非対応のため、指示は user メッセージに埋め込む
        instruction = self.cfg.system_prompt

        translated_texts = []
        for text in texts:
            # 空文字の場合は、空文字を返す
            if not text:
                translated_texts.append("")
                continue

            user_prompt = f"{instruction}\n\n{text}"

            messages: List[Dict[str, Any]] = [
                {"role": "user", "content": user_prompt},
            ]

            # LMに送信
            res = self.client.chat.completions.create(
                model=self.cfg.model,
                messages=messages,
                max_tokens=self.cfg.max_tokens,
                temperature=self.cfg.temperature,
            )
            try:
                res = res.choices[0].message.content
                logging.info(f"翻訳完了: {res}")
                translated_texts.append(res)
            except Exception:
                logging.error("翻訳失敗")
                translated_texts.append("")

        # モデルの破棄
        self.client.close()

        return translated_texts
