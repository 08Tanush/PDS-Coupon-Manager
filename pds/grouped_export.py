import csv
import os
from .grouped_journal import meta

FIELDS=['hospital','hospital_prefix','doctor_reference','code','percent','status','error']

def export(db,path):
    info=meta(db)
    results=[]
    for suffix,all_rows in [('.csv',False),('_audit.csv',True)]:
        target=path.with_name(path.stem+suffix)
        temp=target.with_name(target.name+'.tmp')
        fd=os.open(temp,os.O_CREAT|os.O_TRUNC|os.O_WRONLY,0o600)
        with os.fdopen(fd,'w',newline='',encoding='utf-8') as file:
            writer=csv.DictWriter(file,fieldnames=FIELDS)
            writer.writeheader()
            for code,pct,status,error in db.execute('SELECT code,percent,status,error FROM codes ORDER BY code'):
                if all_rows or status=='CREATED':
                    writer.writerow({'hospital':info['hospital'],'hospital_prefix':info['prefix'],'doctor_reference':info['doctor'], 'code':code,'percent':pct,'status':status,'error':error})
            file.flush();os.fsync(file.fileno())
        os.replace(temp,target)
        results.append(target)
    return results
