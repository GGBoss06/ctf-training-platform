"""在独立演示库上运行：python -m unittest discover -s tests -v。

会写入测试数据；请先使用专用 MySQL 实例导入 database/ctf_init.sql。
"""
import os
import re
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src' / 'web'))
from app import create_app
from db import call, query


@unittest.skipUnless(os.getenv('CTF_RUN_INTEGRATION') == '1', '设置 CTF_RUN_INTEGRATION=1 并连接专用演示库')
class WebIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({'TESTING': True, 'SECRET_KEY': 'integration-test-only'})

    def setUp(self):
        self.client = self.app.test_client()

    def post(self, path, values=None):
        self.client.get('/login')
        with self.client.session_transaction() as sess:
            token = sess['csrf_token']
        return self.client.post(path, data={'csrf_token': token, **(values or {})}, follow_redirects=True)

    def login(self, username='admin', password='Admin@123'):
        response = self.post('/login', {'username': username, 'password': password})
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertIn('uid', sess)

    def test_01_public_and_security(self):
        for path in ['/login', '/register', '/challenges', '/challenges/1', '/ranking']:
            self.assertEqual(self.client.get(path).status_code, 200)
        response = self.client.get('/challenges?q=Welcome&category=Pwn&difficulty=1')
        self.assertIn('Welcome Pwn', response.get_data(as_text=True))
        self.assertNotIn('ret2libc 基础', response.get_data(as_text=True))
        self.assertNotIn('FlagHash', response.get_data(as_text=True))
        self.assertEqual(self.client.get('/challenges?difficulty=99').status_code, 400)
        self.assertEqual(self.client.get('/challenges/14').status_code, 404)
        self.assertEqual(self.client.post('/login', data={'username': 'admin'}).status_code, 400)
        self.assertEqual(self.client.get('/admin/users').status_code, 302)
        self.login('zhangsan', 'Pass@123')
        self.assertEqual(self.client.get('/admin/users').status_code, 403)
        self.assertEqual(self.post('/admin/challenges/1/delete').status_code, 403)
        injection = self.client.get('/challenges?q=%27%20OR%201%3D1--')
        self.assertNotIn('Welcome Pwn', injection.get_data(as_text=True))

    def test_02_register_profile(self):
        values = {'username': 'integration_user', 'password': 'Test@123', 'email': 'integration@example.com'}
        self.assertIn('注册成功', self.post('/register', values).get_data(as_text=True))
        self.assertIn('已被占用', self.post('/register', values).get_data(as_text=True))
        self.login('integration_user', 'Test@123')
        self.assertIn('资料已保存', self.post('/profile', {'email': 'changed@example.com'}).get_data(as_text=True))
        self.assertIn('当前密码不正确', self.post('/profile', {'email': 'changed@example.com', 'new_password': 'Changed@123', 'current_password': 'wrong'}).get_data(as_text=True))
        self.post('/profile', {'email': 'changed@example.com', 'new_password': 'Changed@123', 'current_password': 'Test@123'})
        self.login('integration_user', 'Changed@123')
        with self.app.app_context():
            user = query('SELECT * FROM Users WHERE Username=%s', ('integration_user',), one=True)
            self.assertEqual(user['Email'], 'changed@example.com')
            self.assertNotEqual(user['PasswordHash'], 'Changed@123')

    def test_03_admin_crud_and_audit(self):
        self.login()
        values = {'cid': '2', 'title': '集成测试草稿', 'description': '<script>alert(1)</script>', 'difficulty': '2', 'score': '123', 'flag': 'flag{integration}', 'attachment': ''}
        self.assertIn('已录入', self.post('/admin/challenges/new', values).get_data(as_text=True))
        with self.app.app_context():
            chid = query('SELECT Chid FROM Challenges WHERE Title=%s', (values['title'],), one=True)['Chid']
        values.update(title='集成测试修改', score='150', flag='')
        self.assertIn('已更新', self.post(f'/admin/challenges/{chid}/edit', values).get_data(as_text=True))
        self.assertIn('草稿已删除', self.post(f'/admin/challenges/{chid}/delete').get_data(as_text=True))
        self.assertIn('仅能删除', self.post('/admin/challenges/1/delete').get_data(as_text=True))
        self.assertIn('已上架', self.post('/admin/challenges/14/publish').get_data(as_text=True))
        page = self.client.get('/challenges/14')
        self.assertEqual(page.status_code, 200)
        self.assertIn('已下线', self.post('/admin/challenges/14/offline').get_data(as_text=True))
        self.assertEqual(self.client.get('/challenges/14').status_code, 404)
        self.assertIn('删除草稿', self.client.get('/admin/logs').get_data(as_text=True))

    def test_04_judging_and_duplicate(self):
        self.login('xuer', 'Pass@123')
        self.assertIn('flag 不正确', self.post('/challenges/1', {'flag': 'flag{wrong}'}).get_data(as_text=True))
        self.assertIn('判定正确', self.post('/challenges/1', {'flag': 'flag{w3lc0me_pwn}'}).get_data(as_text=True))
        self.assertIn('不重复计分', self.post('/challenges/1', {'flag': 'flag{w3lc0me_pwn}'}).get_data(as_text=True))
        self.assertIn('flag 不正确', self.post('/challenges/1', {'flag': 'flag{wrong_again}'}).get_data(as_text=True))
        with self.app.app_context():
            score = query('SELECT SUM(ScoreAwarded) AS score FROM Solves WHERE Uid=11', one=True)
            self.assertEqual(score['score'], 100)
            last = query('SELECT IsCorrect FROM Submissions WHERE Uid=11 ORDER BY Subid DESC LIMIT 1', one=True)
            self.assertEqual(last['IsCorrect'], 0)

    def test_05_concurrent_scoring(self):
        with self.app.app_context():
            uid = call('sp_register_user', ('parallel_user', 'Test@123', 'parallel@example.com'), ('uid', 'result', 'message'))['uid']

        def submit(chid=4):
            with self.app.app_context():
                flag = 'flag{sql_1nj3ct10n}' if chid == 4 else 'flag{c4es4r_c1ph3r}'
                return call('sp_submit_flag', (uid, chid, flag), ('result', 'score', 'message'))

        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(submit, [4] * 6))
        self.assertEqual(sum(r['result'] == 'correct' for r in results), 1)
        self.assertEqual(sum(r['result'] == 'duplicate' for r in results), 5)
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(submit, [4, 10]))
        with self.app.app_context():
            rows = query('SELECT TotalAfter FROM ScoreLogs WHERE Uid=%s ORDER BY LogId', (uid,))
            self.assertEqual([r['TotalAfter'] for r in rows], [200, 300])

    def test_06_disabled_account(self):
        self.login('xuer', 'Pass@123')
        admin = self.app.test_client()
        admin.get('/login')
        with admin.session_transaction() as sess:
            token = sess['csrf_token']
        admin.post('/login', data={'csrf_token': token, 'username': 'admin', 'password': 'Admin@123'})
        admin.get('/admin/users')
        with admin.session_transaction() as sess:
            token = sess['csrf_token']
        admin.post('/admin/users', data={'csrf_token': token, 'uid': 11, 'status': 'disabled'})
        self.assertEqual(self.client.get('/profile').status_code, 302)
        self.post('/login', {'username': 'xuer', 'password': 'Pass@123'})
        with self.client.session_transaction() as sess:
            self.assertNotIn('uid', sess)


if __name__ == '__main__':
    unittest.main(verbosity=2)
