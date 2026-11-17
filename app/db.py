"""SQLite storage: raw entries (long format) and the live prediction log."""
import os
import sqlite3
from datetime import datetime

from .config import ROOT

DB_PATH = os.environ.get("HABIT_DB", str(ROOT / "data.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student TEXT NOT NULL,
    timestamp TEXT NOT NULL,   -- when it was logged
    date TEXT NOT NULL,        -- the day it belongs to (YYYY-MM-DD)
    field TEXT NOT NULL,
    value REAL NOT NULL        -- a choice is stored as the option's position
);
CREATE TABLE IF NOT EXISTS predictions (
    student TEXT NOT NULL,
    target_date TEXT NOT NULL,
    model TEXT NOT NULL,
    predicted REAL NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (student, target_date, model)
);
"""


def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def now():
    return datetime.now().isoformat(timespec="seconds")


def add_entry(student, date, field, value, timestamp=None, replace=False):
    """replace=True: the field holds one entry per day, so the new one replaces
    any earlier entry of that day (rollup 'last')."""
    with connect() as con:
        if replace:
            con.execute("DELETE FROM entries WHERE student = ? AND date = ? AND field = ?",
                        (student, date, field))
        cur = con.execute(
            "INSERT INTO entries (student, timestamp, date, field, value) VALUES (?,?,?,?,?)",
            (student, timestamp or now(), date, field, float(value)))
        return cur.lastrowid


def delete_entry(student, entry_id):
    with connect() as con:
        con.execute("DELETE FROM entries WHERE id = ? AND student = ?", (entry_id, student))


def entries(student, date=None):
    sql = "SELECT * FROM entries WHERE student = ?"
    args = [student]
    if date:
        sql += " AND date = ?"
        args.append(date)
    with connect() as con:
        return [dict(r) for r in con.execute(sql + " ORDER BY date, timestamp, id", args)]


def entry_counts(student):
    """{field: number of entries} for one student."""
    with connect() as con:
        return {r["field"]: r["n"] for r in con.execute(
            "SELECT field, COUNT(*) AS n FROM entries WHERE student = ? GROUP BY field", (student,))}


def replace_student(student, rows):
    """Wipe a student's entries and insert new ones (used by the seed)."""
    with connect() as con:
        con.execute("DELETE FROM entries WHERE student = ?", (student,))
        con.executemany(
            "INSERT INTO entries (student, timestamp, date, field, value) VALUES (?,?,?,?,?)",
            [(student, r["timestamp"], r["date"], r["field"], float(r["value"])) for r in rows])


def save_prediction(student, target_date, model, predicted):
    """One prediction per model per target date. Saving again before the target
    date has started replaces it; the caller only ever predicts tomorrow."""
    with connect() as con:
        con.execute(
            "INSERT OR REPLACE INTO predictions VALUES (?,?,?,?,?)",
            (student, target_date, model, float(predicted), now()))


def predictions(student):
    with connect() as con:
        return [dict(r) for r in con.execute(
            "SELECT * FROM predictions WHERE student = ? ORDER BY target_date, model", (student,))]
