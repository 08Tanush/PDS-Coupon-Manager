"""Dashboard adapter around the existing durable batch engine."""
from pathlib import Path
from types import SimpleNamespace
import sqlite3
import uuid
from .grouped_batch import start, resume
from .grouped_journal import meta
from .hospitals import abbreviation


def create_batch(folder, hospital, count, short='', doctor='', confirm=False):
    folder=Path(folder)
    if not hospital.strip():
        raise ValueError('Hospital name is required')
    if not 1 <= int(count) <= 5000:
        raise ValueError('Count must be 1-5000')
    folder.mkdir(parents=True,exist_ok=True)
    path=folder / ('batch_'+uuid.uuid4().hex+'.sqlite3')
    args=SimpleNamespace(hospital=hospital.strip(), count=int(count),short=short.strip() or None,
                         doctor_reference=doctor.strip(),ends_at=None,journal=str(path),confirm=confirm)
    result=start(args)
    return path,result


def batch_details(path):
    path=Path(path)
    with sqlite3.connect(path) as db:
        info=meta(db)
        counts=dict(db.execute('SELECT status, COUNT(*) FROM codes GROUP BY status'))
        by_percent=dict(db.execute('SELECT percent,COUNT(*) FROM codes GROUP BY percent'))
    return {'id':path.stem,'hospital':info['hospital'],'prefix':info['prefix'],
            'doctor':info.get('doctor',''),'start':info['start'],'counts':counts,
            'by_percent':by_percent,'total':sum(counts.values())}


def list_batches(folder):
    paths=sorted(Path(folder).glob('batch_*.sqlite3'),key=lambda p:p.stat().st_mtime,reverse=True)
    items=[]
    for path in paths:
        try: items.append(batch_details(path))
        except (sqlite3.Error,KeyError,ValueError): continue
    return items


def get_batch_path(folder, batch_id):
    import re
    if not re.fullmatch(r'batch_[0-9a-f]{32}',batch_id):
        raise ValueError('Invalid batch identifier')
    path=Path(folder)/(batch_id+'.sqlite3')
    if not path.is_file():
        raise FileNotFoundError('Batch not found')
    return path


def dashboard_stats(batches):
    total = sum(b['total'] for b in batches)
    created = sum(b['counts'].get('CREATED', 0) for b in batches)
    percent_sum = sum(sum(int(pct) * count for pct, count in b['by_percent'].items()) for b in batches)
    return {'batches': len(batches), 'coupons': total, 'created': created,
            'success_rate': round(created * 100 / total, 1) if total else 0,
            'average_discount': round(percent_sum / total, 1) if total else 0}
