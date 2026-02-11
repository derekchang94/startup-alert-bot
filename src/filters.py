"""공고 필터링 모듈 - 스타트업 / 해외진출 관련 공고만 선별

회사 정보:
- 서울 서초구 소재 스타트업 (IT 서비스)
- 일본 도쿄 법인 운영 중 (해외진출 진행)

필터링 정책:
1. 스타트업 또는 해외진출 관련 키워드 매칭
2. 지방 한정 공고 배제 (특정 지역 소재 기업만 지원 가능한 공고)
   - 단, 지방에서 시행하더라도 전국 대상이면 포함
"""
import re
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
    "혁신기업", "기술창업", "소셜벤처",
    "중소기업", "중소벤처",
]

# 해외진출 관련 키워드 (일본/도쿄 법인 상황 반영)
GLOBAL_KEYWORDS = [
    "해외진출", "해외", "글로벌", "수출",
    "해외마케팅", "해외시장", "글로벌진출",
    "해외전시", "국제", "무역", "통상",
    "바이어", "수출바우처", "해외인증",
    "K-Startup", "글로벌창업",
    "현지화", "해외투자", "global",
    "일본", "Japan", "도쿄", "Tokyo", "동경",
    "아시아", "동남아", "해외법인",
    "해외지사", "해외수출", "해외판로",
    "수출지원", "해외개척", "수출상담",
]

ALL_KEYWORDS = STARTUP_KEYWORDS + GLOBAL_KEYWORDS

# ── 지역 제한 배제 필터 ──

# 수도권 (서울 서초구 기업이 참여 가능한 지역)
METRO_AREA = [
    "서울", "경기", "인천", "수도권",
]

# 지방 지역명 (이 지역 소재 기업 '한정' 공고는 배제)
REGIONAL_AREAS = [
    "부산", "대구", "광주", "대전", "울산", "세종",
    "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
    "충청", "전라", "경상",
    "강릉", "춘천", "원주", "청주", "천안", "전주", "목포",
    "순천", "여수", "포항", "구미", "김해", "창원", "진주",
    "제주시", "서귀포",
]

# 지역 한정을 나타내는 패턴 (지역명 + 이 패턴 → 배제 대상)
REGIONAL_RESTRICTION_PATTERNS = [
    r"소재\s*(기업|업체|중소|스타트업|창업)",
    r"(에|에만|만)\s*소재",
    r"(내|도내|시내|권내)\s*(기업|업체|소재|등록|본사)",
    r"(기업|업체|본사|사업장).*한정",
    r"(기업|업체|본사|사업장).*제한",
    r"(기업|업체|본사|사업장).*대상$",
    r"(에|도|시|군)\s*위치한",
    r"지역\s*(기업|업체|소재|한정)",
    r"관내\s*(기업|업체|소재)",
]

# 전국 대상임을 나타내는 키워드 (이 키워드가 있으면 지역 제한 배제 안 함)
NATIONWIDE_KEYWORDS = [
    "전국", "제한없음", "제한 없음", "무관",
    "전 지역", "전지역", "지역무관", "지역 무관",
    "누구나", "전체 기업", "전체기업",
]


def _is_region_restricted(posting: dict) -> bool:
    """지방 한정 공고인지 판별

    True를 반환하면 배제 대상 (서울 서초구 기업이 참여 불가능)
    """
    searchable = " ".join([
        posting.get("title", ""),
        posting.get("target", ""),
        posting.get("summary", ""),
        posting.get("organization", ""),
    ])

    if not searchable.strip():
        return False

    # 1) 전국 대상 키워드가 있으면 무조건 포함
    for kw in NATIONWIDE_KEYWORDS:
        if kw in searchable:
            return False

    # 2) 서울/수도권 관련이면 포함
    for area in METRO_AREA:
        if area in searchable:
            return False

    # 3) 지방 지역명 + 제한 패턴 조합 검사
    for area in REGIONAL_AREAS:
        if area not in searchable:
            continue

        # 지역명이 단순 언급(시행기관 등)이 아니라 대상 제한인지 확인
        for pattern in REGIONAL_RESTRICTION_PATTERNS:
            full_pattern = f"{area}.*{pattern}|{pattern}.*{area}"
            if re.search(full_pattern, searchable):
                logger.debug(f"지역 제한 배제: [{area}] {posting.get('title', '')}")
                return True

        # 제목에 "[지역명]" 형태로 지역이 포함되고, 타겟에도 해당 지역만 언급
        title = posting.get("title", "")
        target = posting.get("target", "")
        if (
            re.search(rf"\[{area}\]|\({area}\)|{area}지역|{area}도|{area}시", title)
            and area in target
            and not any(m in target for m in METRO_AREA)
            and not any(n in target for n in NATIONWIDE_KEYWORDS)
        ):
            logger.debug(f"지역 제한 배제 (제목+타겟): [{area}] {title}")
            return True

    return False


def filter_relevant_postings(postings: List[dict]) -> List[dict]:
    """스타트업 또는 해외진출 관련 공고만 필터링 + 지역 제한 공고 배제"""
    keyword_matched = []
    region_excluded = 0

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
            keyword_matched.append(posting)

    # 키워드 매칭된 공고 중 지역 제한 공고 배제
    filtered = []
    for posting in keyword_matched:
        if _is_region_restricted(posting):
            region_excluded += 1
        else:
            filtered.append(posting)

    logger.info(
        f"필터링 결과: {len(postings)}건 중 키워드 매칭 {len(keyword_matched)}건, "
        f"지역 제한 배제 {region_excluded}건 → 최종 {len(filtered)}건"
    )
    return filtered
