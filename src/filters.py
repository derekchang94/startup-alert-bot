"""공고 필터링 모듈 - 스타트업 / 해외진출 관련 공고만 선별"""
import logging
from typing import List

logger = logging.getLogger(__name__)

# 스타트업 관련 키워드
STARTUP_KEYWORDS = [
    "스타트업", "창업", "초기창업", "예비창업", "벤처",
    "창업기업", "창업자", "창업지원", "창업패키지",
    "액셀러레이", "인큐베이", "보육", "TIPS",
    "스케일업", "scale-up", "startup",
    "사업화", "비즈쿨", "창업도약",
    "에코스타트업", "재도전",
]

# 해외진출 관련 키워드
GLOBAL_KEYWORDS = [
    "해외진출", "해외", "글로벌", "수출",
    "해외마케팅", "해외시장", "글로벌진출",
    "해외전시", "국제", "무역", "통상",
    "바이어", "수출바우처", "해외인증",
    "K-Startup", "글로벌창업",
    "현지화", "해외투자", "global",
]

ALL_KEYWORDS = STARTUP_KEYWORDS + GLOBAL_KEYWORDS


def filter_relevant_postings(postings: List[dict]) -> List[dict]:
    """스타트업 또는 해외진출 관련 공고만 필터링"""
    filtered = []

    for posting in postings:
        # 제목, 카테고리, 지원대상, 요약에서 키워드 매칭
        searchable = " ".join([
            posting.get("title", ""),
            posting.get("category", ""),
            posting.get("target", ""),
            posting.get("summary", ""),
        ]).lower()

        matched = [kw for kw in ALL_KEYWORDS if kw.lower() in searchable]

        if matched:
            posting["_matched_keywords"] = matched
            filtered.append(posting)

    logger.info(
        f"필터링 결과: {len(postings)}건 중 {len(filtered)}건 선별 "
        f"(스타트업/해외진출 관련)"
    )
    return filtered
