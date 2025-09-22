from typing import List
from datetime import datetime, timedelta, timezone, date
import re
import requests
import feedparser

from domain.models import Paper


class ArxivService:
    def _extract_arxiv_id(self, s: str) -> str | None:
        """
        文字列から arXiv の識別子を抽出する。
        サポート:
        - 新形式: 2101.12345 または 2101.12345v2
        - 旧形式: astro-ph/0601001 または astro-ph/0601001v2
        - URL: https://arxiv.org/abs/<id>, https://arxiv.org/pdf/<id>.pdf など
        """
        try:
            s = (s or "").strip()
            if not s:
                return None
            # URL から抽出
            m = re.search(
                r"arxiv\.org/(abs|pdf|html)/([^\s?#/]+)",
                s,
            )
            if m:
                ident = m.group(2)
                ident = re.sub(r"\.pdf$", "", ident, flags=re.IGNORECASE)
                return ident
            # 新形式 ID
            if re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)?", s):
                return s
            # 旧形式 ID (例: astro-ph/0601001)
            if re.fullmatch(r"[a-zA-Z\-\.]+/\d{7}(v\d+)?", s):
                return s
        except Exception:
            pass
        return None

    def _fetch_entries_by_id_list(
        self,
        ids: list[str],
        max_results: int,
    ) -> list:
        """id_list で arXiv API から entries を取得（最大 max_results 件まで）"""
        if not ids:
            return []
        url = "http://export.arxiv.org/api/query"
        # arXiv API は id_list をカンマ区切りで指定
        params = {
            # 念のためサイズを制限
            "id_list": ",".join(ids)[:2048],
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        return getattr(feed, "entries", [])

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
        # キーワードを arXiv ID/URL と テキスト に分離
        ids: list[str] = []
        text_terms: list[str] = []
        for kw in keywords:
            if not kw:
                continue
            arx_id = self._extract_arxiv_id(str(kw))
            if arx_id:
                ids.append(arx_id)
            else:
                text_terms.append(str(kw))

        entries = []
        # 1) id_list で取得
        if ids:
            entries.extend(self._fetch_entries_by_id_list(ids, max_results))

        # 2) テキスト検索（abs: に対する OR）
        if text_terms:
            url = "http://export.arxiv.org/api/query"
            query = "+OR+".join([f"abs:{kw}" for kw in text_terms])
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
            entries.extend(getattr(feed, "entries", []))

        # 相対日付の解釈と範囲正規化（空文字は無期限として扱う）
        if not start_date:
            start_d = date.min
        else:
            start_d = self._parse_relative_jp(start_date)

        if not end_date:
            end_d = date.max
        else:
            end_d = self._parse_relative_jp(end_date)
        if end_d < start_d:
            start_d, end_d = end_d, start_d

        # 重複排除（idでユニーク化）
        seen_ids: set[str] = set()
        papers: List[Paper] = []
        for e in entries:
            pub_raw = e.get("published", "")
            try:
                fmt = "%Y-%m-%dT%H:%M:%SZ"
                published_dt = datetime.strptime(pub_raw, fmt).replace(
                    tzinfo=timezone.utc
                )
            except Exception:
                published_dt = None
            if published_dt is not None and not self._within_range(
                published_dt, start_d, end_d
            ):
                continue
            pid = e.get("id", "")
            if pid in seen_ids:
                continue
            seen_ids.add(pid)
            papers.append(self._entry_to_paper(e))

        return papers
