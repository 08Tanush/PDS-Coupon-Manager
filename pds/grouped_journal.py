import json
import sqlite3
from pathlib import Path

def open_new(path, info, rows):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        raise ValueError(f'Journal already exists: {path}. Use resume instead.')
    db = sqlite3.connect(path)
    db.execute('PRAGMA busy_timeout=5000')
    db.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
    db.execute('CREATE TABLE parents(percent INTEGER PRIMARY KEY,seed TEXT NOT NULL,discount_id TEXT, state TEXT NOT NULL DEFAULT "PLANNED")')
    db.execute('CREATE TABLE codes(code TEXT PRIMARY KEY,percent INTEGER NOT NULL,status TEXT NOT NULL DEFAULT "PLANNED",error TEXT NOT NULL DEFAULT "",job_id TEXT)')
    with db:
        db.executemany('INSERT INTO metadata VALUES (?,?)',[(k,json.dumps(v)) for k,v in info.items()])
        db.executemany('INSERT INTO codes(code,percent) VALUES (?,?)',rows)
        for pct in sorted({pct for _,pct in rows}):
            seed = next(code for code,p in rows if p == pct)
            db.execute('INSERT INTO parents(percent,seed) VALUES (?,?)',(pct,seed))
    return db

def meta(db):
    return {key:json.loads(value) for key,value in db.execute('SELECT key,value FROM metadata')}

def update(db,code,status,error='',job_id=None):
    with db:
        db.execute('UPDATE codes SET status=?,error=?,job_id=COALESCE(?,job_id) WHERE code=?',(status,error[:300],job_id,code))
