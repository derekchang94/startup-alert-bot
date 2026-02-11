"""Database 모듈 테스트"""
import os
import tempfile

import pytest

# 테스트 전에 sys.path 설정
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import Database


@pytest.fixture
def db():
    """임시 DB로 테스트"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database = Database(db_path=path)
    yield database
    database.close()
    os.unlink(path)


@pytest.fixture
def sample_posting():
    return {
        "id": "test_001",
        "title": "2026년 초기창업패키지",
        "organization": "중소벤처기업부",
        "category": "창업",
        "start_date": "2026-02-10",
        "end_date": "2026-03-15",
        "target": "예비창업자",
        "url": "https://example.com/1",
        "summary": "초기 창업기업 지원",
        "source": "bizinfo",
    }


def test_insert_new_posting(db, sample_posting):
    assert db.insert_posting(sample_posting) is True


def test_insert_duplicate_posting(db, sample_posting):
    db.insert_posting(sample_posting)
    assert db.insert_posting(sample_posting) is False


def test_get_unnotified(db, sample_posting):
    db.insert_posting(sample_posting)
    unnotified = db.get_unnotified_postings()
    assert len(unnotified) == 1
    assert unnotified[0]["title"] == "2026년 초기창업패키지"


def test_mark_as_notified(db, sample_posting):
    db.insert_posting(sample_posting)
    db.mark_as_notified(["test_001"])
    unnotified = db.get_unnotified_postings()
    assert len(unnotified) == 0


def test_generate_id():
    id1 = Database.generate_id("공고A", "https://a.com")
    id2 = Database.generate_id("공고B", "https://b.com")
    id3 = Database.generate_id("공고A", "https://a.com")
    assert id1 != id2
    assert id1 == id3


def test_stats(db, sample_posting):
    db.insert_posting(sample_posting)
    stats = db.get_stats()
    assert stats["total"] == 1
    assert stats["pending"] == 1
    assert stats["by_source"]["bizinfo"] == 1
