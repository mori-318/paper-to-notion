import os
from notion_client import Client

from domain.models import Paper

class NotionService:
    def __init__(self):
        api_key = os.getenv("NOTION_API_KEY", "")
        database_id = os.getenv("NOTION_DATABASE_ID", "")
        # 必須チェック（未設定だと 401 になりやすいので明示）
        if not api_key or not database_id:
            raise EnvironmentError("NOTION_API_KEY または NOTION_DATABASE_ID が未設定です。")

        # Notion-Version を 2022-06-28 に固定（ユーザーの正常動作例に合わせる）
        self.client = Client(auth=api_key, notion_version="2022-06-28")
        self.database_id = database_id

    def create_page(self, paper: Paper) -> bool:
        """
        Notionに論文を保存する
        Args:
            paper (Paper): 保存する論文オブジェクト
        Returns:
            bool: 保存に成功したかどうか
        """
        try:
            self.client.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "名前": {"title": [{"text": {"content": paper.title}}]},
                    "Progress": {"status": {"name": "未読"}},
                    "Authors": {"rich_text": [{"text": {"content": ", ".join(paper.authors)}}]},
                    "Time": {"rich_text": [{"text": {"content": str(paper.published_date)}}]},
                    "URL": {"url": paper.url},
                },
            )
            return True
        except Exception:
            return False