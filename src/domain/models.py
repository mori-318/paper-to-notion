from pydantic import BaseModel
from typing import List

class Paper(BaseModel):
    """
    Paper model
    - title: str
    - url: str
    - authors: List[str]
    - published_date: str  # 日付文字列（ISO形式など）
    - category: str
    - abstract: str
    - abstract_ja: str (ローカルLMによる翻訳後)
    """
    title: str
    url: str
    authors: List[str]
    published_date: str  # 日付文字列（ISO形式など）
    category: str
    abstract: str
    abstract_ja: str