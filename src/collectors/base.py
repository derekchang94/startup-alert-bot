"""수집기 기본 클래스"""
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import requests

from src.config import Config

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """모든 수집기의 기본 클래스"""

    SOURCE_NAME: str = "unknown"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "StartupAlertBot/1.0 (startup-support-monitor; educational)",
            "Accept": "application/json, application/xml, text/html",
        })
        self.delay = Config.REQUEST_DELAY

    @abstractmethod
    def collect(self) -> List[dict]:
        """
        공고 데이터를 수집하여 표준 형식의 dict 리스트로 반환.

        각 dict 필수 키:
        - id: 고유 식별자
        - title: 공고명
        - organization: 소관기관
        - category: 분야
        - start_date: 신청 시작일 (YYYY-MM-DD)
        - end_date: 신청 종료일 (YYYY-MM-DD)
        - target: 지원대상
        - url: 상세 URL
        - summary: 사업 요약
        - source: 데이터 소스명
        """
        pass

    def _request(self, url: str, params: Optional[dict] = None,
                 max_retries: int = 3) -> requests.Response:
        """재시도 로직 포함 HTTP GET 요청"""
        for attempt in range(max_retries):
            try:
                if attempt > 0 or self.delay > 0:
                    time.sleep(self.delay)
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(
                    f"[{self.SOURCE_NAME}] 요청 실패 (시도 {attempt + 1}/{max_retries}): {e}"
                )
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """날짜 형식 정규화 -> YYYY-MM-DD"""
        if not date_str:
            return ""
        cleaned = date_str.strip().replace(".", "").replace("/", "").replace("-", "")
        if len(cleaned) == 8 and cleaned.isdigit():
            return f"{cleaned[:4]}-{cleaned[4:6]}-{cleaned[6:8]}"
        return date_str.strip()
