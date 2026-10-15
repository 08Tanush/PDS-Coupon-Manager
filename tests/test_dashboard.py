import tempfile
import unittest
from pathlib import Path
from web_app import create_app
from pds.dashboard_service import create_batch, list_batches

class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.app=create_app({'TESTING':True,'SECRET_KEY':'test-secret','PDS_ADMIN_PASSWORD':'test-pass',
                             'PDS_OUTPUT_DIR':self.tmp.name})
        self.client=self.app.test_client()

    def tearDown(self): self.tmp.cleanup()

    def test_login_required(self):
        self.assertEqual(self.client.get('/').status_code,302)
        self.assertEqual(self.client.get('/login').status_code,200)

    def test_wrong_password(self):
        with self.client.session_transaction() as sess: sess['csrf']='test-token'
        response=self.client.post('/login',data={'csrf':'test-token','password':'wrong'})
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.client.get('/').status_code,302)

    def test_login_and_csrf(self):
        with self.client.session_transaction() as sess: sess['csrf']='test-token'
        self.client.post('/login',data={'csrf':'test-token','password':'test-pass'})
        self.assertEqual(self.client.get('/').status_code,200)
        self.assertEqual(self.client.post('/generate',data={}).status_code,400)

    def test_dry_run_does_not_write(self):
        path,result=create_batch(self.tmp.name,'Tata Memorial Hospital',5,confirm=False)
        self.assertEqual(result,0)
        self.assertFalse(path.exists())
        self.assertEqual(list_batches(self.tmp.name),[])

    def test_invalid_count(self):
        with self.assertRaises(ValueError): create_batch(self.tmp.name,'Hospital',5001)

    def test_invalid_batch_id(self):
        with self.client.session_transaction() as sess: sess['admin']=True
        self.assertEqual(self.client.get('/batches/../../.env').status_code,404)

class DashboardStatsTests(unittest.TestCase):
    def test_stats_are_derived_from_actual_batches(self):
        from pds.dashboard_service import dashboard_stats
        batches=[{'total':5,'counts':{'CREATED':4,'FAILED':1},'by_percent':{6:2,7:2,8:1}}]
        result=dashboard_stats(batches)
        self.assertEqual(result['batches'],1)
        self.assertEqual(result['coupons'],5)
        self.assertEqual(result['success_rate'],80)
        self.assertEqual(result['average_discount'],6.8)
