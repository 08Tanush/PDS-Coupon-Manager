import argparse
import sqlite3
import sys
from pds.grouped_batch import start,resume

def main():
    parser=argparse.ArgumentParser(description='Hospital-wise grouped Shopify coupon generator')
    commands=parser.add_subparsers(dest='command',required=True)
    create=commands.add_parser('create')
    create.add_argument('--hospital',required=True)
    create.add_argument('--short',help='Optional hospital abbreviation override')
    create.add_argument('--count',type=int,default=100)
    create.add_argument('--doctor-reference',default='')
    create.add_argument('--ends-at',help='ISO-8601 datetime with timezone; default 90 days')
    create.add_argument('--journal',default='output/hospital_batch.sqlite3')
    create.add_argument('--confirm',action='store_true')
    recovery=commands.add_parser('resume')
    recovery.add_argument('--journal',default='output/hospital_batch.sqlite3')
    recovery.add_argument('--confirm',action='store_true')
    args=parser.parse_args()
    try:
        return start(args) if args.command=='create' else resume(args.journal,args.confirm)
    except (RuntimeError,ValueError,sqlite3.Error,OSError,KeyError) as exc:
        print('ERROR:',exc,file=sys.stderr)
        return 1

if __name__=='__main__':
    sys.exit(main())
