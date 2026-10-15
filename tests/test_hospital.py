import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pds.hospitals import abbreviation,plan
from pds.grouped_journal import open_new,update
from pds.grouped_export import export

class HospitalTests(unittest.TestCase):
    def test_abbreviation(self):
        self.assertEqual(abbreviation('Tata Memorial Hospital'),'TMH')
        self.assertEqual(abbreviation('Kokilaben Dhirubhai Ambani Hospital'),'KDAH')
    def test_independent_random_assignment(self):
        from secrets import choice as original_choice
        with patch('pds.hospitals.secrets.choice',side_effect=lambda items: 8 if isinstance(items,tuple) else original_choice(items)):
            rows=plan('Tata Memorial Hospital',5)
        self.assertEqual(len(rows),5)
        self.assertTrue(all(code.startswith('TMH-') and pct==8 for code,pct in rows))
    def test_distribution_range_and_unique(self):
        rows=plan('Tata Memorial Hospital',500)
        self.assertEqual(len({c for c,p in rows}),500)
        self.assertTrue(all(p in (6,7,8) for c,p in rows))
    def test_grouped_journal_and_export(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'batch.sqlite3'
            info={'hospital':'Tata Memorial Hospital','prefix':'TMH','doctor':'','store':'example.myshopify.com'}
            db=open_new(path,info,[('TMH-ABC',6),('TMH-DEF',8)])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM parents').fetchone()[0],2)
            update(db,'TMH-ABC','CREATED')
            good,audit=export(db,path)
            self.assertIn('TMH-ABC',good.read_text())
            self.assertNotIn('TMH-DEF',good.read_text())
            self.assertIn('TMH-DEF',audit.read_text())
            db.close()

if __name__=='__main__':unittest.main()

class ProcessingTests(unittest.TestCase):
    def test_parent_payload_and_bulk_codes(self):
        from pds.discount_service import make_discount
        from pds.grouped_shopify import add_codes
        payload=make_discount('TMH-ABC',7,'2026-10-15T00:00:00+00:00','2026-11-15T00:00:00+00:00')
        self.assertEqual(payload['customerGets']['value']['percentage'],.07)
        self.assertEqual(payload['usageLimit'],1)
        with patch('pds.grouped_shopify.graphql',return_value={'discountRedeemCodeBulkAdd':{'bulkCreation':{'id':'job1'},'userErrors':[]}}) as graphql_mock:
            self.assertEqual(add_codes('store','token','parent1',['TMH-A','TMH-B']),'job1')
            self.assertEqual(graphql_mock.call_args.args[3]['codes'],[{'code':'TMH-A'},{'code':'TMH-B'}])

    def test_bulk_job_only_exports_confirmed(self):
        from pds.grouped_batch import reconcile_jobs
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'batch.sqlite3'
            info={'hospital':'Tata Memorial Hospital','prefix':'TMH','doctor':'','store':'example.myshopify.com'}
            db=open_new(path,info,[('TMH-ABC',6),('TMH-DEF',6)])
            with db:
                db.execute('UPDATE codes SET status="SUBMITTED",job_id="job1"')
            result={'done':True,'codes':{'nodes':[
                {'code':'TMH-ABC','discountRedeemCode':{'id':'r1'},'errors':[]},
                {'code':'TMH-DEF','discountRedeemCode':None,'errors':[{'message':'Duplicate'}]}]}}
            with patch('pds.grouped_batch.job_status',return_value=result):
                reconcile_jobs(db,'store','token',6)
            self.assertEqual(dict(db.execute('SELECT code,status FROM codes'))['TMH-ABC'],'CREATED')
            self.assertEqual(dict(db.execute('SELECT code,status FROM codes'))['TMH-DEF'],'FAILED')
            good,audit=export(db,path)
            self.assertNotIn('TMH-DEF',good.read_text())
            db.close()
