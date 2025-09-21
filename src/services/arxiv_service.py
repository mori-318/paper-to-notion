from typing import List
from datetime import datetime, timedelta, timezone, date
import re
import requests
import feedparser

from domain.models import Paper

class ArxivService:
    def _parse_relative_jp(self, expr: str) -> date:
        """
        「X年Y月Z日前」の形式を今日からの相対日付に変換
        欠損は0として扱う
        例: "1年0月0日前" -> 今日から365日引いた日（簡易換算）
        Args:
            expr (str): 「X年Y月Z日前」の形式
        Returns:
            date: 今日からの相対日付
        """
        nums = re.findall(r"(\d+)", expr)
        y = int(nums[0]) if len(nums) > 0 else 0
        m = int(nums[1]) if len(nums) > 1 else 0
        d = int(nums[2]) if len(nums) > 2 else 0
        days = y * 365 + m * 30 + d  # 簡易換算
        return datetime.now().date() - timedelta(days=days)

    def _within_range(self, pub: datetime, start_d: date, end_d: date) -> bool:
        """
        期間内かどうかを判定
        Args:
            pub (datetime): 論文の発表日
            start_d (date): 開始日
            end_d (date): 終了日
        Returns:
            bool: 期間内かどうか
        """
        pub_d = pub.date()
        return start_d <= pub_d <= end_d

    def _entry_to_paper(self, e) -> Paper:
        """
        検索結果をPaperモデルに変換
        Args:
            e (FeedParserDict): arXivのRSSエントリ
        Returns:
            Paper: 変換後のPaperモデル
        """
        id = e.get("id", "").strip()
        title = e.get("title", "").strip()
        link = e.get("link", "")
        authors = [a.get("name", "") for a in e.get("authors", [])]
        published_raw = e.get("published", "")
        try:
            published_dt = datetime.strptime(published_raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            published_iso = published_dt.isoformat()
        except Exception:
            published_iso = published_raw
        category = ""
        if hasattr(e, "tags") and e.tags:
            try:
                category = ",".join(t.get("term", "") for t in e.tags)
            except Exception:
                pass
        abstract = e.get("summary", "").strip()
        return Paper(
            id=id,
            title=title,
            url=link,
            authors=authors,
            published_date=published_iso,
            category=category,
            abstract=abstract,
            abstract_ja="",
        )

    def search_papers(
        self,
        keywords: List[str],
        max_results: int,
        start_date: str,
        end_date: str,
    ) -> List[Paper]:
        """
        arXiv API を使って論文を検索する

        Args:
            keywords (List[str]): 検索キーワード
            max_results (int): 最大検索数
            start_date (str): 検索開始（例: "1年0月0日前"）
            end_date (str): 検索終了（例: "0年0月0日前"）

        Returns:
            List[Paper]: 検索結果リスト
        """
        # クエリ構築（abs: に対する OR）
        terms = [f"abs:{kw}" for kw in keywords if kw]
        if not terms:
            return []
        query = "+OR+".join(terms)

        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)

        # 相対日付の解釈と範囲正規化
        start_d = self._parse_relative_jp(start_date)
        end_d = self._parse_relative_jp(end_date)
        if end_d < start_d:
            start_d, end_d = end_d, start_d

        papers: List[Paper] = []
        for e in feed.entries:
            pub_raw = e.get("published", "")
            try:
                # ISO8601形式の日時文字列をUTCに変換
                published_dt = datetime.strptime(pub_raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except Exception:
                published_dt = None
            if published_dt is not None and not self._within_range(published_dt, start_d, end_d):
                continue
            papers.append(self._entry_to_paper(e))

        return papers