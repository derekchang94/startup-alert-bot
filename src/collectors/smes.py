"""중소벤처24 공고정보 API 수집기

중소벤처24 API: 중소벤처기업부 유관기관 공고정보
- 공공데이터포털 표준 응답 구조 (response > body > items > item)
- 주의: data.go.kr의 Encoding 키에는 %2F 등이 포함되어 있어 이중인코딩 방지 필요
"""
import logging
import urllib.parse
from typing import List

from src.config import Config
from src.collectors.base import BaseCollector
from src.database import Database

logger = logging.getLogger(__name__)

SMES_API_URL = "https://apis.data.go.kr/B552735/smes24AnncInfoService/getAnncList"


class SmesCollector(BaseCollector):
    """중소벤처24 공고정보 수집기"""

    SOURCE_NAME = "smes24"

    def collect(self) -> List[dict]:
        logger.info("중소벤처24 API 수집 시작")
        postings = []

        try:
            # data.go.kr Encoding 키는 이미 URL 인코딩되어 있으므로
            # 디코딩 후 params에 전달 (requests가 다시 인코딩함)
            decoded_key = urllib.parse.unquote(Config.SMES_API_KEY)

            params = {
                "serviceKey": decoded_key,
                "pageNo": 1,
                "numOfRows": Config.COLLECT_COUNT,
                "type": "json",
            }

            response = self._request(SMES_API_URL, params=params)
            data = response.json()

            body = data.get("response", {}).get("body", {})
            items = body.get("items", {})

            if isinstance(items, dict):
                items = items.get("item", [])
            if isinstance(items, dict):
                items = [items]
            if not isinstance(items, list):
                items = []

            for item in items:
                title = item.get("anncNm", "").strip()
                url = item.get("anncUrl", "").strip()
                if not title:
                    continue

                postings.append({
                    "id": item.get("anncId") or Database.generate_id(title, url),
                    "title": title,
                    "organization": item.get("cntcInsttNm", "").strip(),
                    "category": item.get("anncClssNm", "").strip(),
                    "start_date": self._normalize_date(item.get("rcptBgngDt", "")),
                    "end_date": self._normalize_date(item.get("rcptEndDt", "")),
                    "target": item.get("trgtNm", "").strip(),
                    "url": url,
                    "summary": item.get("anncSumry", "").strip(),
                    "source": self.SOURCE_NAME,
                })

        except Exception as e:
            logger.error(f"중소벤처24 API 수집 실패: {e}")

        logger.info(f"중소벤처24 수집 완료: {len(postings)}건")
        return postings
