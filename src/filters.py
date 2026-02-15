"""공고 필터링 모듈 - 스타트업 / 해외진출 관련 공고만 선별

회사 정보:
- 서울 서초구 소재 스타트업 (IT 서비스)
- 일본 도쿄 법인 운영 중 (해외진출 진행)

필터링 정책:
1. 스타트업 또는 해외진출 관련 키워드 매칭
2. 지방/경기 한정 공고 배제 (서울 소재 기업만 지원 가능한 공고만 포함)
   - 단, 지방에서 시행하더라도 전국 대상이면 포함
3. 만료(종료일 경과) 또는 과거 연도 공고 배제
"""
import re
import logging
from datetime import datetime, date
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

# 서울권만 허용 (서울 서초구 기업이 참여 가능한 지역)
# 주의: 경기, 인천은 서울과 별개이므로 METRO_AREA에서 제외
METRO_AREA = [
    "서울", "수도권",
]

# 지방 + 경기/인천 지역명 (이 지역 소재 기업 '한정' 공고는 배제)
REGIONAL_AREAS = [
    "경기", "인천",
    "부산", "대구", "광주", "대전", "울산", "세종",
    "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
    "충청", "전라", "경상",
    "강릉", "춘천", "원주", "청주", "천안", "전주", "목포",
    "순천", "여수", "포항", "구미", "김해", "창원", "진주",
    "제주시", "서귀포",
    "경기도", "인천시", "인천광역시",
    "부산광역시", "대구광역시", "광주광역시", "대전광역시", "울산광역시",
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
    r"(도|시|군|구)\s*소재",
    r"지역\s*내\s",
    r"(입주|등록|소재).*기업",
]

# 전국 대상임을 나타내는 키워드 (이 키워드가 있으면 지역 제한 배제 안 함)
NATIONWIDE_KEYWORDS = [
    "전국", "제한없음", "제한 없음", "무관",
    "전 지역", "전지역", "지역무관", "지역 무관",
    "누구나", "전체 기업", "전체기업",
]


def _is_expired_or_outdated(posting: dict) -> bool:
    """만료되었거나 과거 연도의 공고인지 확인

    True를 반환하면 배제 대상
    """
    today = date.today()

    end_date_str = posting.get("end_date", "").strip()
    start_date_str = posting.get("start_date", "").strip()

    # D-day 형식 (thevc 등)은 검증 스킵
    if end_date_str and not re.match(r"^\d{4}-\d{2}-\d{2}$", end_date_str):
        return False

    # end_date가 있고 이미 지난 경우 → 만료
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            if end_date < today:
                logger.debug(f"만료 공고 배제: {posting.get('title', '')} (마감: {end_date_str})")
                return True
        except ValueError:
            pass

    # start_date가 작년 이전이고 end_date가 없거나 작년인 경우 → 오래된 공고
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            if start_date.year < today.year:
                # end_date도 없거나 작년이면 배제
                if not end_date_str:
                    logger.debug(f"과거 연도 공고 배제: {posting.get('title', '')} (시작: {start_date_str})")
                    return True
                try:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                    if end_date.year < today.year:
                        logger.debug(f"과거 연도 공고 배제: {posting.get('title', '')} ({start_date_str}~{end_date_str})")
                        return True
                except ValueError:
                    return True
        except ValueError:
            pass

    return False


def _is_region_restricted(posting: dict) -> bool:
    """지방/경기 한정 공고인지 판별

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

    # 3) 지방/경기/인천 지역명 + 제한 패턴 조합 검사
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
    """스타트업 또는 해외진출 관련 공고만 필터링

    필터링 순서:
    1. 만료/과거 연도 공고 배제
    2. 키워드 매칭 (스타트업/해외진출)
    3. 지역 제한 공고 배제 (경기/지방 한정)
    """
    # 1단계: 만료/과거 연도 공고 제거
    date_valid = []
    date_excluded = 0
    for posting in postings:
        if _is_expired_or_outdated(posting):
            date_excluded += 1
        else:
            date_valid.append(posting)

    # 2단계: 키워드 매칭
    keyword_matched = []
    for posting in date_valid:
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

    # 3단계: 지역 제한 공고 배제
    filtered = []
    region_excluded = 0
    for posting in keyword_matched:
        if _is_region_restricted(posting):
            region_excluded += 1
        else:
            filtered.append(posting)

    logger.info(
        f"필터링 결과: 전체 {len(postings)}건 → "
        f"만료/과거 배제 {date_excluded}건, "
        f"키워드 매칭 {len(keyword_matched)}건, "
        f"지역 제한 배제 {region_excluded}건 → "
        f"최종 {len(filtered)}건"
    )
    return filtered
