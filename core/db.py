"""SQLite storage, schema upgrades, and first-run demo seeding."""
import json
import sqlite3
from datetime import datetime, timedelta

from config import DB_PATH


def connect():
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_column(connection, name, definition):
    columns = {row[1] for row in connection.execute("PRAGMA table_info(reports)")}
    if name not in columns:
        connection.execute(f"ALTER TABLE reports ADD COLUMN {name} {definition}")


def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS reports(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            location TEXT NOT NULL,
            lat REAL,
            lon REAL,
            categories TEXT NOT NULL,
            item_count INTEGER NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Reported',
            image_path TEXT,
            notes TEXT,
            is_demo INTEGER NOT NULL DEFAULT 0,
            priority_score INTEGER NOT NULL DEFAULT 0,
            severity TEXT NOT NULL DEFAULT 'Moderate',
            overflowing INTEGER NOT NULL DEFAULT 0,
            sensitive_site INTEGER NOT NULL DEFAULT 0
        )""")
        con.execute("CREATE TABLE IF NOT EXISTS scans(id INTEGER PRIMARY KEY AUTOINCREMENT,timestamp TEXT NOT NULL,is_demo INTEGER NOT NULL DEFAULT 0)")
        # Safe in-place migration for databases created by earlier prototypes.
        _ensure_column(con, "priority_score", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(con, "severity", "TEXT NOT NULL DEFAULT 'Moderate'")
        _ensure_column(con, "overflowing", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(con, "sensitive_site", "INTEGER NOT NULL DEFAULT 0")

        if con.execute("SELECT count(*) FROM reports WHERE is_demo=1").fetchone()[0] == 0:
            now = datetime.now()
            places = [
                ("Riverside Park",19.076,72.877),("Market Street",19.081,72.881),
                ("Central Bus Stop",19.070,72.869),("School Lane",19.085,72.872),
                ("Lake View",19.091,72.890),("Community Garden",19.064,72.884),
                ("Old Town Square",19.073,72.858),("Station Road",19.080,72.862),
                ("Canal Walk",19.095,72.866),("Library Corner",19.068,72.875),
                ("West Playground",19.060,72.865),("Harbor Approach",19.055,72.889),
                ("North Avenue",19.100,72.879),("Clinic Junction",19.088,72.853),
                ("Civic Plaza",19.077,72.895),
            ]
            categories = [
                ["plastic","paper"],["plastic","organic"],["general"],["paper","metal"],
                ["plastic","glass"],["organic"],["general","plastic"],["paper"],
                ["plastic","metal","general"],["glass","plastic"],["organic","paper"],
                ["general","plastic"],["metal","plastic"],["paper","organic"],["plastic","general"],
            ]
            for index, (place, lat, lon) in enumerate(places):
                timestamp = (now - timedelta(days=14-index)).isoformat(timespec="seconds")
                priority = ["High","Medium","Low"][index % 3]
                status = "Resolved" if index in (1,4,7,10) else "In Progress" if index in (2,8,13) else "Reported"
                con.execute("""INSERT INTO reports(timestamp,location,lat,lon,categories,item_count,priority,status,image_path,notes,is_demo,severity,overflowing,sensitive_site)
                    VALUES(?,?,?,?,?,?,?,?,?,?,1,'Moderate',0,?)""",
                    (timestamp,place,lat,lon,json.dumps(categories[index]),3+index%8,priority,status,None,
                     "DEMO DATA - illustrative sample report",int(index in (3,9,13))))
        if con.execute("SELECT count(*) FROM scans").fetchone()[0] == 0:
            for index in range(32):
                stamp = (datetime.now()-timedelta(days=index%21)).isoformat(timespec="seconds")
                con.execute("INSERT INTO scans(timestamp,is_demo) VALUES(?,1)",(stamp,))


def create_report(location, lat, lon, categories, item_count, priority, image_path, notes="", is_demo=False,
                  priority_score=0, severity="Moderate", overflowing=False, sensitive_site=False):
    with connect() as con:
        cursor = con.execute("""INSERT INTO reports(timestamp,location,lat,lon,categories,item_count,priority,status,image_path,notes,is_demo,priority_score,severity,overflowing,sensitive_site)
            VALUES(?,?,?,?,?,?,?,'Reported',?,?,?,?,?,?,?)""",
            (datetime.now().isoformat(timespec="seconds"),location,lat,lon,json.dumps(categories),item_count,priority,
             image_path,notes,int(is_demo),int(priority_score),severity,int(overflowing),int(sensitive_site)))
        con.execute("INSERT INTO scans(timestamp,is_demo) VALUES(?,?)",(datetime.now().isoformat(timespec="seconds"),int(is_demo)))
        return cursor.lastrowid


def list_reports():
    with connect() as con:
        return [dict(row) for row in con.execute("SELECT * FROM reports ORDER BY timestamp DESC")]


def update_status(report_id, status):
    if status not in {"Reported","In Progress","Resolved"}:
        raise ValueError("Invalid report status")
    with connect() as con:
        con.execute("UPDATE reports SET status=? WHERE id=?",(status,report_id))


def scan_count(is_demo=None):
    with connect() as con:
        if is_demo is None:
            return con.execute("SELECT count(*) FROM scans").fetchone()[0]
        return con.execute("SELECT count(*) FROM scans WHERE is_demo=?",(int(is_demo),)).fetchone()[0]


def record_scan(is_demo=False):
    with connect() as con:
        con.execute("INSERT INTO scans(timestamp,is_demo) VALUES(?,?)",(datetime.now().isoformat(timespec="seconds"),int(is_demo)))
