"""SQLite 데이터베이스 관리 모듈"""
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.config import Config


class Database:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or Config.DB_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS postings (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                organization TEXT,
                category TEXT,
                start_date TEXT,
                end_date TEXT,
                target TEXT,
                url TEXT,
                summary TEXT,
                source TEXT,
                collected_at TEXT NOT NULL,
                notified_at TEXT,
                is_notified INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_postings_notified
                ON postings(is_notified);
            CREATE INDEX IF NOT EXISTS idx_postings_end_date
                ON postings(end_date);
            CREATE INDEX IF NOT EXISTS idx_postings_collected
                ON postings(collected_at);
        """)
        self.conn.commit()

    @staticmethod
    def generate_id(title: str, url: str) -> str:
        """공고 고유 ID 생성 (제목+URL 해시)"""
        return hashlib.md5(f"{title}:{url}".encode()).hexdigest()

    def insert_posting(self, posting: dict) -> bool:
        """공고 삽입. 신규이면 True, 중복이면 False 반환."""
        cursor = self.conn.execute("SELECT 1 FROM postings WHERE id = ?", (posting["id"],))
        if cursor.fetchone():
            return False

        self.conn.execute("""
            INSERT INTO postings
            (id, title, organization, category, start_date, end_date,
             target, url, summary, source, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            posting["id"],
            posting["title"],
            posting.get("organization", ""),
            posting.get("category", ""),
            posting.get("start_date", ""),
            posting.get("end_date", ""),
            posting.get("target", ""),
            posting.get("url", ""),
            posting.get("summary", ""),
            posting.get("source", ""),
            datetime.now().isoformat(),
        ))
        self.conn.commit()
        return True

    def get_unnotified_postings(self) -> List[dict]:
        """아직 알림을 보내지 않은 공고 목록 조회"""
        cursor = self.conn.execute("""
            SELECT * FROM postings
            WHERE is_notified = 0
            ORDER BY collected_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

    def mark_as_notified(self, posting_ids: List[str]):
        """공고들을 알림 완료로 표시"""
        now = datetime.now().isoformat()
        self.conn.executemany(
            "UPDATE postings SET is_notified = 1, notified_at = ? WHERE id = ?",
            [(now, pid) for pid in posting_ids],
        )
        self.conn.commit()

    def get_expiring_soon(self, days: int = 3) -> List[dict]:
        """마감 임박 공고 조회 (D-N일 이내)"""
        cursor = self.conn.execute("""
            SELECT * FROM postings
            WHERE end_date != ''
              AND date(end_date) BETWEEN date('now') AND date('now', ? || ' days')
            ORDER BY end_date ASC
        """, (str(days),))
        return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> dict:
        """수집 통계"""
        total = self.conn.execute("SELECT COUNT(*) FROM postings").fetchone()[0]
        notified = self.conn.execute("SELECT COUNT(*) FROM postings WHERE is_notified = 1").fetchone()[0]
        sources = self.conn.execute(
            "SELECT source, COUNT(*) as cnt FROM postings GROUP BY source"
        ).fetchall()
        return {
            "total": total,
            "notified": notified,
            "pending": total - notified,
            "by_source": {row["source"]: row["cnt"] for row in sources},
        }

    def close(self):
        self.conn.close()
