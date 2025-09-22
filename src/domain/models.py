from pydantic import BaseModel
from typing import List, Optional


class SearchConfig(BaseModel):
    """
    検索リクエスト
    - keyword: str
    - max_results: int
    - start_date: str
    - end_date: str
    - notion_database_name: Optional[str]
    """
    keyword: List[str]
    max_results: int = 10
    start_date: str = "1y0m0w0d"
    end_date: str = "0y0m0w0d"
    notion_database_name: Optional[str] = None


class Paper(BaseModel):
    """
    Paper model
    - id: str
    - title: str
    - url: str
    - authors: List[str]
    - published_date: str  # 日付文字列（ISO形式など）
    - category: str
    - abstract: str
    - abstract_ja: str (ローカルLMによる翻訳後)
    """
    id: str
    title: str
    url: str
    authors: List[str]
    published_date: str  # 日付文字列（ISO形式など）
    category: str
    abstract: str
    abstract_ja: str
