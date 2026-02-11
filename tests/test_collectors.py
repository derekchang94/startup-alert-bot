"""Collectors 모듈 테스트"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collectors.base import BaseCollector


def test_normalize_date():
    """날짜 정규화 테스트"""
    assert BaseCollector._normalize_date("20260210") == "2026-02-10"
    assert BaseCollector._normalize_date("2026.02.10") == "2026-02-10"
    assert BaseCollector._normalize_date("2026/02/10") == "2026-02-10"
    assert BaseCollector._normalize_date("2026-02-10") == "2026-02-10"
    assert BaseCollector._normalize_date("") == ""
    assert BaseCollector._normalize_date("상시접수") == "상시접수"
