"""Notifier 모듈 테스트"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.notifier import SlackNotifier


def test_build_posting_blocks():
    """개별 공고 블록 생성 테스트"""
    notifier = SlackNotifier()
    posting = {
        "title": "테스트 공고",
        "organization": "테스트 기관",
        "category": "창업",
        "start_date": "2026-02-10",
        "end_date": "2026-03-15",
        "target": "예비창업자",
        "url": "https://example.com/1",
        "summary": "테스트 요약",
    }
    blocks = notifier._build_posting_blocks(posting, index=1, total=5)
    assert len(blocks) > 0
    section_texts = [
        b["text"]["text"] for b in blocks if b.get("type") == "section"
    ]
    assert any("테스트 공고" in t for t in section_texts)
