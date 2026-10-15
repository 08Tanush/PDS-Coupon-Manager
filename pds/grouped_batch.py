import os
import sqlite3
import sys
import time
from datetime import datetime,timedelta,timezone
from pathlib import Path
from .config import STORE,load_env
from .shopify_client import authenticate,graphql,QUERY
from .hospitals import plan,abbreviation
from .grouped_journal import open_new,meta,update
from .grouped_shopify import create_parent,lookup,add_codes,job_status
from .grouped_export import export


def start(args):
    rows=plan(args.hospital,args.count,args.short)
    prefix=rows[0][0].split('-')[0]
    journal=Path(args.journal)
    if journal.suffix!='.sqlite3':
        raise ValueError('Journal must have .sqlite3 extension')
    if journal.exists():
        raise ValueError('Existing journal; choose another name or resume')
    if not args.confirm:
        counts={pct:sum(p==pct for _,p in rows) for pct in (6,7,8)}
        print('DRY RUN | Hospital:',args.hospital,'| Prefix:',prefix,'| Count:',len(rows),'| Random distribution:',counts)
        print('No Shopify changes. Use --confirm to create a journal and issue codes.')
        return 0
    now=datetime.now(timezone.utc)
    if args.ends_at:
        expiry=datetime.fromisoformat(args.ends_at.replace('Z','+00:00'))
        if expiry.tzinfo is None or expiry<=now:
            raise ValueError('Expiry must be a future timezone-aware ISO datetime')
    else:
        expiry=now+timedelta(days=90)
    info={'hospital':args.hospital.strip(),'prefix':prefix,'doctor':args.doctor_reference or '',
          'start':now.isoformat(timespec='seconds'),'expiry':expiry.isoformat(timespec='seconds'),'store':STORE}
    db=open_new(journal,info,rows)
    db.close()
    print('Saved durable coupon plan:',journal)
    return resume(journal,True)


def resume(path,confirm=False):
    path=Path(path)
    if not path.exists():
        raise ValueError(f'Journal missing: {path}')
    db=sqlite3.connect(path)
    try:
        if not confirm:
            print('READ ONLY:',dict(db.execute('SELECT status,COUNT(*) FROM codes GROUP BY status')))
            print('Use resume --confirm to continue.')
            return 0
        return process(db,path)
    finally:
        db.close()


def process(db,path):
    info=meta(db)
    if info['store']!=STORE:
        raise RuntimeError('Journal belongs to a different Shopify store')
    lock=path.with_suffix('.lock')
    try:
        fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        os.close(fd)
    except FileExistsError:
        raise RuntimeError('Journal locked. Verify no other process is running before removing stale lock.') from None
    try:
        load_env()
        store,token=authenticate()
        shop=graphql(store,token,QUERY)['shop']
        if shop['myshopifyDomain']!=STORE:
            raise RuntimeError('Shopify store identity mismatch')
        print('Connected:',shop['name'])
        for pct,seed,did,state in db.execute('SELECT percent,seed,discount_id,state FROM parents ORDER BY percent').fetchall():
            title=f"PDS | {info['prefix']} | {info['hospital']} | {pct}%"
            if state!='READY':
                found=lookup(store,token,seed)
                if found:
                    basic=found.get('codeDiscount') or {}
                    if basic.get('title')!=title or basic.get('usageLimit')!=1:
                        raise RuntimeError(f'Existing seed {seed} does not match this batch. Manual review required.')
                    did=found['id']
                elif state=='ATTEMPTING':
                    raise RuntimeError(f'Parent {pct}% creation ambiguous. Verify Shopify Admin before retry.')
                else:
                    with db:
                        db.execute('UPDATE parents SET state="ATTEMPTING" WHERE percent=?',(pct,))
                    did=create_parent(store,token,seed,title,pct,info['start'],info['expiry'])
                with db:
                    db.execute('UPDATE parents SET state="READY",discount_id=? WHERE percent=?',(did,pct))
                    db.execute('UPDATE codes SET status="CREATED" WHERE code=?',(seed,))
                print('Parent ready:',title)
            # A parent creation succeeded earlier but code state update may have been interrupted.
            update(db,seed,'CREATED')
            reconcile_jobs(db,store,token,pct)
            # Only send codes never previously attempted; uncertain submissions are never repeated blindly.
            remaining=[code for (code,) in db.execute('SELECT code FROM codes WHERE percent=? AND status="PLANNED" ORDER BY code',(pct,))]
            for offset in range(0,len(remaining),100):
                chunk=remaining[offset:offset+100]
                # Persist the in-flight state before the network request.
                with db:
                    db.executemany('UPDATE codes SET status="SENDING" WHERE code=?',[(c,) for c in chunk])
                try:
                    job=add_codes(store,token,did,chunk)
                except Exception:
                    print('Bulk submission ambiguous; inspect/resume without resending automatically.',file=sys.stderr)
                    raise
                with db:
                    db.executemany('UPDATE codes SET status="SUBMITTED",job_id=? WHERE code=?',[(job,c) for c in chunk])
                print(f'Submitted {len(chunk)} codes to {pct}% parent; job {job}')
                reconcile_jobs(db,store,token,pct)
                time.sleep(0.5)
        results=export(db,path)
        counts=dict(db.execute('SELECT status,COUNT(*) FROM codes GROUP BY status'))
        print('Status:',counts,'\nVerified codes CSV:',results[0],'\nAudit CSV:',results[1])
        if counts.get('CREATED',0)!=sum(counts.values()):
            print('Some codes pending/unknown. Do NOT distribute non-CREATED codes.',file=sys.stderr)
            return 2
        return 0
    finally:
        export(db,path)
        lock.unlink(missing_ok=True)


def reconcile_jobs(db,store,token,pct):
    jobs=[job for (job,) in db.execute('SELECT DISTINCT job_id FROM codes WHERE percent=? AND status="SUBMITTED" AND job_id IS NOT NULL',(pct,))]
    for job in jobs:
        result=None
        for _ in range(10):
            result=job_status(store,token,job)
            if result and result.get('done'):
                break
            time.sleep(1)
        if not result or not result.get('done'):
            print('Async job still pending:',job)
            continue
        nodes=(result.get('codes') or {}).get('nodes') or []
        expected={code for (code,) in db.execute('SELECT code FROM codes WHERE job_id=?',(job,))}
        for node in nodes:
            code=node['code']
            if code not in expected:
                continue
            if node.get('discountRedeemCode'):
                update(db,code,'CREATED')
            else:
                update(db,code,'FAILED',str(node.get('errors') or 'Shopify import failed'))
        unresolved=expected-{n['code'] for n in nodes}
        for code in unresolved:
            update(db,code,'UNKNOWN','Job completed without per-code result; manual verification required')
    # SENDING is intentionally not retried: submission may have reached Shopify.
