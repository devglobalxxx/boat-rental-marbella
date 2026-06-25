"""SQLite cache for scraped leads — dedupe, resume, avoid re-fetching."""
from __future__ import annotations
import pathlib, sqlite3, json, datetime, contextlib

DB_PATH = pathlib.Path(__file__).resolve().parents[2] / "data" / "scraper" / "leads.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    domain         TEXT PRIMARY KEY,
    company        TEXT,
    city           TEXT,
    country        TEXT,
    emails         TEXT,
    phones         TEXT,
    contact_form   TEXT,
    source         TEXT,
    first_seen     TEXT,
    last_enriched  TEXT,
    confidence     INTEGER DEFAULT 0,
    pushed_to_sheet INTEGER DEFAULT 0,
    raw            TEXT
);
CREATE TABLE IF NOT EXISTS fetched_urls (
    url        TEXT PRIMARY KEY,
    fetched_at TEXT,
    status     INTEGER
);
CREATE TABLE IF NOT EXISTS seeds (
    domain   TEXT,
    city     TEXT,
    country  TEXT,
    source   TEXT,
    company  TEXT,
    found_at TEXT,
    PRIMARY KEY (domain, source, city)
);
"""

def connect():
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)
    con.execute("PRAGMA journal_mode=WAL")
    return con

def now():
    return datetime.datetime.utcnow().isoformat(timespec="seconds")

def add_seed(con, domain, city, country, source, company=""):
    domain = domain.lower().lstrip(".")
    with contextlib.suppress(sqlite3.IntegrityError):
        con.execute(
            "INSERT INTO seeds(domain,city,country,source,company,found_at) VALUES(?,?,?,?,?,?)",
            (domain, city, country, source, company, now()),
        )
    con.execute(
        "INSERT OR IGNORE INTO leads(domain,city,country,source,company,first_seen) VALUES(?,?,?,?,?,?)",
        (domain, city, country, source, company, now()),
    )
    con.commit()

def mark_url(con, url, status):
    con.execute("INSERT OR REPLACE INTO fetched_urls(url,fetched_at,status) VALUES(?,?,?)",
                (url, now(), status))
    con.commit()

def url_seen(con, url):
    return con.execute("SELECT 1 FROM fetched_urls WHERE url=?", (url,)).fetchone() is not None

def domains_needing_enrichment(con, limit=500):
    return con.execute(
        "SELECT domain,city,country,company FROM leads WHERE last_enriched IS NULL LIMIT ?", (limit,)
    ).fetchall()

def save_enrichment(con, domain, emails, phones, contact_form, confidence):
    con.execute(
        "UPDATE leads SET emails=?, phones=?, contact_form=?, confidence=?, last_enriched=? WHERE domain=?",
        (json.dumps(sorted(set(emails))), json.dumps(sorted(set(phones))),
         contact_form, confidence, now(), domain),
    )
    con.commit()

def unpushed_leads(con):
    return con.execute(
        """SELECT domain,company,city,country,emails,phones,contact_form,source,first_seen,confidence
           FROM leads WHERE pushed_to_sheet=0 AND last_enriched IS NOT NULL"""
    ).fetchall()

def mark_pushed(con, domains):
    con.executemany("UPDATE leads SET pushed_to_sheet=1 WHERE domain=?", [(d,) for d in domains])
    con.commit()

def stats(con):
    out = {}
    out["leads"] = con.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    out["enriched"] = con.execute("SELECT COUNT(*) FROM leads WHERE last_enriched IS NOT NULL").fetchone()[0]
    out["with_email"] = con.execute("SELECT COUNT(*) FROM leads WHERE emails NOT IN ('','[]') AND emails IS NOT NULL").fetchone()[0]
    out["pushed"] = con.execute("SELECT COUNT(*) FROM leads WHERE pushed_to_sheet=1").fetchone()[0]
    return out
