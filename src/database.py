"""
SQLite database layer for tracking jobs and applications.
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'jobs.db')


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id          TEXT UNIQUE,          -- platform-specific ID
            title           TEXT NOT NULL,
            company         TEXT NOT NULL,
            location        TEXT,
            job_type        TEXT,                 -- full-time, contract, etc.
            salary          TEXT,
            platform        TEXT,                 -- linkedin, indeed, workday, manual
            url             TEXT,
            description     TEXT,
            posted_date     TEXT,
            found_date      TEXT DEFAULT CURRENT_TIMESTAMP,

            -- Classification
            role_type       TEXT,                 -- management, ic, unknown
            match_score     REAL DEFAULT 0,       -- 0-100 match percentage
            matched_skills  TEXT,                 -- JSON list of matched skills
            resume_type     TEXT,                 -- executive, cloud, it_manager, contract
            is_indian_firm  INTEGER DEFAULT 0,
            flagged_reason  TEXT,

            -- Application status
            status          TEXT DEFAULT 'new',   -- new, queued, applying, applied, skipped, failed
            applied_date    TEXT,
            notes           TEXT,

            -- Q&A
            qa_pairs        TEXT                  -- JSON list of {q, a} pairs
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            searched_at TEXT DEFAULT CURRENT_TIMESTAMP,
            platform    TEXT,
            keywords    TEXT,
            location    TEXT,
            jobs_found  INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()


# ── Job CRUD ──────────────────────────────────────────────

def upsert_job(job: dict) -> int:
    """Insert or update a job. Returns the row id."""
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        INSERT INTO jobs (job_id, title, company, location, job_type, salary,
                          platform, url, description, posted_date,
                          role_type, match_score, matched_skills, resume_type,
                          is_indian_firm, flagged_reason, status, notes)
        VALUES (:job_id, :title, :company, :location, :job_type, :salary,
                :platform, :url, :description, :posted_date,
                :role_type, :match_score, :matched_skills, :resume_type,
                :is_indian_firm, :flagged_reason, :status, :notes)
        ON CONFLICT(job_id) DO UPDATE SET
            title        = excluded.title,
            match_score  = excluded.match_score,
            matched_skills = excluded.matched_skills,
            resume_type  = excluded.resume_type,
            is_indian_firm = excluded.is_indian_firm,
            flagged_reason = excluded.flagged_reason
    ''', {
        'job_id':        job.get('job_id', ''),
        'title':         job.get('title', ''),
        'company':       job.get('company', ''),
        'location':      job.get('location', ''),
        'job_type':      job.get('job_type', ''),
        'salary':        job.get('salary', ''),
        'platform':      job.get('platform', ''),
        'url':           job.get('url', ''),
        'description':   job.get('description', ''),
        'posted_date':   job.get('posted_date', ''),
        'role_type':     job.get('role_type', 'unknown'),
        'match_score':   job.get('match_score', 0),
        'matched_skills': json.dumps(job.get('matched_skills', [])),
        'resume_type':   job.get('resume_type', 'it_manager'),
        'is_indian_firm': 1 if job.get('is_indian_firm') else 0,
        'flagged_reason': job.get('flagged_reason', ''),
        'status':        job.get('status', 'new'),
        'notes':         job.get('notes', ''),
    })
    row_id = c.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_jobs(status=None, limit=100, offset=0):
    conn = get_conn()
    c = conn.cursor()
    if status:
        rows = c.execute(
            'SELECT * FROM jobs WHERE status=? ORDER BY found_date DESC LIMIT ? OFFSET ?',
            (status, limit, offset)
        ).fetchall()
    else:
        rows = c.execute(
            'SELECT * FROM jobs ORDER BY found_date DESC LIMIT ? OFFSET ?',
            (limit, offset)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_job_by_id(row_id: int):
    conn = get_conn()
    row = conn.execute('SELECT * FROM jobs WHERE id=?', (row_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_job_status(row_id: int, status: str, notes: str = None):
    conn = get_conn()
    if notes:
        conn.execute('UPDATE jobs SET status=?, notes=? WHERE id=?', (status, notes, row_id))
    else:
        conn.execute('UPDATE jobs SET status=? WHERE id=?', (status, row_id))
    if status == 'applied':
        conn.execute('UPDATE jobs SET applied_date=? WHERE id=?',
                     (datetime.now().isoformat(), row_id))
    conn.commit()
    conn.close()


def save_qa_pairs(row_id: int, qa_pairs: list):
    conn = get_conn()
    conn.execute('UPDATE jobs SET qa_pairs=? WHERE id=?',
                 (json.dumps(qa_pairs), row_id))
    conn.commit()
    conn.close()


def is_duplicate(url: str) -> bool:
    conn = get_conn()
    row = conn.execute('SELECT id FROM jobs WHERE url=?', (url,)).fetchone()
    conn.close()
    return row is not None


def get_stats():
    conn = get_conn()
    stats = {}
    for status in ['new', 'queued', 'applied', 'skipped', 'failed']:
        row = conn.execute('SELECT COUNT(*) as cnt FROM jobs WHERE status=?', (status,)).fetchone()
        stats[status] = row['cnt']
    stats['total'] = sum(stats.values())
    stats['indian_firm'] = conn.execute(
        'SELECT COUNT(*) as cnt FROM jobs WHERE is_indian_firm=1').fetchone()['cnt']
    stats['management'] = conn.execute(
        'SELECT COUNT(*) as cnt FROM jobs WHERE role_type="management"').fetchone()['cnt']
    conn.close()
    return stats


# ── Settings ──────────────────────────────────────────────

def get_setting(key: str, default=None):
    conn = get_conn()
    row = conn.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
    conn.close()
    return row['value'] if row else default


def set_setting(key: str, value: str):
    conn = get_conn()
    conn.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)', (key, value))
    conn.commit()
    conn.close()


def get_all_settings() -> dict:
    conn = get_conn()
    rows = conn.execute('SELECT key, value FROM settings').fetchall()
    conn.close()
    return {r['key']: r['value'] for r in rows}
