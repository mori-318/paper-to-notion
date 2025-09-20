from __future__ import annotations
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import threading

try:
    # llama-cpp-python
    from llama_cpp import Llama
except Exception as e:  # pragma: no cover
    Llama = None  # type: ignore


@dataclass
class TranslationConfig:
    """翻訳モデル設定"""
    repo_id: str = "webbigdata/gemma-2-2b-jpn-it-translate-gguf"
    filename: str = "gemma-2-2b-jpn-it-translate-IQ3_M.gguf"
    # 実行時パラメータ（環境に応じて調整可）
    n_ctx: int = 4096
    n_threads: Optional[int] = None  # None で自動
    n_gpu_layers: int = 20  # CPU のみの場合 0
    # 推論時パラメータ
    temperature: float = 0.2
    top_p: float = 0.95
    max_tokens: int = 2048
    system_prompt: str = "以下の英文を日本語に翻訳し、翻訳した結果のみを出力してください。 例：(入力)This is a test. -> (出力)これはテストです。"


class _LlamaHolder:
    """LLaMAモデルの保持クラス"""
    _instance: Optional["_LlamaHolder"] = None
    _lock = threading.Lock()

    def __init__(self, cfg: TranslationConfig):
        if Llama is None:
            raise RuntimeError("llama-cpp-python がインストールされていません。pyproject.toml に追加し、uv sync を実行してください。")
        self.cfg = cfg
        # モデルロード（推論時パラメータはここでは渡さない）
        self.lm = Llama.from_pretrained(
            repo_id=self.cfg.repo_id,
            filename=self.cfg.filename,
            n_ctx=self.cfg.n_ctx,
            n_threads=self.cfg.n_threads,
            n_gpu_layers=self.cfg.n_gpu_layers,
        )

    @classmethod
    def get(cls, cfg: Optional[TranslationConfig] = None) -> "_LlamaHolder":
        """インスタンスを取得する"""
        if cls._instance is not None:
            return cls._instance
        with cls._lock:
            if cls._instance is None:
                cls._instance = _LlamaHolder(cfg or TranslationConfig())
        return cls._instance


class TranslationService:
    """
    ローカルLM(Swallow-MS)を使った翻訳サービス
    """

    def __init__(self, cfg: Optional[TranslationConfig] = None):
        self.cfg = cfg or TranslationConfig()
        self._holder = _LlamaHolder.get(self.cfg)

    def translate_en_to_jp(self, text: str) -> str:
        """
        英文を日本語に翻訳する
        Args:
            text (str): 翻訳したい英文
        Returns:
            str: 翻訳した日本語
        """
        if not text:
            return ""

        # このモデルは system ロール非対応のため、指示は user メッセージに埋め込む
        instruction = self.cfg.system_prompt
        user_prompt = f"{instruction}\n\n{text}"

        messages: List[Dict[str, Any]] = [
            {"role": "user", "content": user_prompt},
        ]

        # LMに送信
        res = self._holder.lm.create_chat_completion(
            messages=messages,
            max_tokens=self.cfg.max_tokens,
            temperature=self.cfg.temperature,
            top_p=self.cfg.top_p,
        )
        try:
            return res["choices"][0]["message"]["content"].strip()
        except Exception:
            return ""
