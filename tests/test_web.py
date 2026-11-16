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

    def client_post(self, client, path, values=None):
        client.get('/login')
        with client.session_transaction() as sess:
            token = sess['csrf_token']
        return client.post(path, data={'csrf_token': token, **(values or {})}, follow_redirects=True)

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
        self.assertIn('题目已删除', self.post(f'/admin/challenges/{chid}/delete').get_data(as_text=True))
        self.assertIn('删除题目', self.client.get('/admin/logs').get_data(as_text=True))
        # 上架后仍可删除：不再要求题目必须是草稿
        values = {'cid': '4', 'title': '集成测试上架后删除', 'description': '上线后删除', 'difficulty': '2', 'score': '222', 'flag': 'flag{publish_then_delete}', 'attachment': ''}
        self.post('/admin/challenges/new', values)
        with self.app.app_context():
            chid = query('SELECT Chid FROM Challenges WHERE Title=%s', (values['title'],), one=True)['Chid']
        self.assertIn('已上架', self.post(f'/admin/challenges/{chid}/publish').get_data(as_text=True))
        self.assertEqual(self.client.get(f'/challenges/{chid}').status_code, 200)
        # 已产生提交、解题与得分日志后删除，相关记录应被一并清理
        student = self.app.test_client()
        self.client_post(student, '/login', {'username': 'zhangsan', 'password': 'Pass@123'})
        self.client_post(student, f'/challenges/{chid}', {'flag': 'flag{publish_then_delete}'})
        with self.app.app_context():
            self.assertEqual(query('SELECT COUNT(*) AS n FROM Submissions WHERE Chid=%s', (chid,), one=True)['n'], 1)
            self.assertEqual(query('SELECT COUNT(*) AS n FROM Solves WHERE Chid=%s', (chid,), one=True)['n'], 1)
            self.assertEqual(query('SELECT COUNT(*) AS n FROM ScoreLogs WHERE Chid=%s', (chid,), one=True)['n'], 1)
        deleted = self.post(f'/admin/challenges/{chid}/delete').get_data(as_text=True)
        self.assertIn('题目已删除', deleted)
        self.assertIn('清理了 1 条提交记录和 1 条得分记录', deleted)
        with self.app.app_context():
            self.assertIsNone(query('SELECT Chid FROM Challenges WHERE Chid=%s', (chid,), one=True))
            self.assertEqual(query('SELECT COUNT(*) AS n FROM Submissions WHERE Chid=%s', (chid,), one=True)['n'], 0)
            self.assertEqual(query('SELECT COUNT(*) AS n FROM Solves WHERE Chid=%s', (chid,), one=True)['n'], 0)
            self.assertEqual(query('SELECT COUNT(*) AS n FROM ScoreLogs WHERE Chid=%s', (chid,), one=True)['n'], 0)
        self.assertIn('已上架', self.post('/admin/challenges/14/publish').get_data(as_text=True))
        page = self.client.get('/challenges/14')
        self.assertEqual(page.status_code, 200)
        self.assertIn('已下线', self.post('/admin/challenges/14/offline').get_data(as_text=True))
        self.assertEqual(self.client.get('/challenges/14').status_code, 404)

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


    def test_07_admin_user_management(self):
        self.login()
        register = self.app.test_client()
        self.client_post(register, '/register', {'username': 'manage_user', 'password': 'Test@123', 'email': 'manage@example.com'})
        with self.app.app_context():
            user = query('SELECT Uid FROM Users WHERE Username=%s', ('manage_user',), one=True)
        self.assertIsNotNone(user)
        uid = user['Uid']
        page = self.client.get(f'/admin/users/{uid}/edit')
        self.assertEqual(page.status_code, 200)
        self.assertIn('manage_user', page.get_data(as_text=True))
        self.assertIn('重置登录密码', page.get_data(as_text=True))
        self.assertIn('账号资料已更新', self.post(f'/admin/users/{uid}/edit', {'action': 'profile', 'email': 'managed@example.com', 'status': 'disabled'}).get_data(as_text=True))
        with self.app.app_context():
            updated = query('SELECT Email,Status FROM Users WHERE Uid=%s', (uid,), one=True)
            self.assertEqual(updated['Email'], 'managed@example.com')
            self.assertEqual(updated['Status'], 'disabled')
        self.assertIn('两次输入的新密码不一致', self.post(f'/admin/users/{uid}/edit', {'action': 'password', 'password': 'NewPass@123', 'confirm_password': 'Other@1234'}).get_data(as_text=True))
        self.assertIn('已重置 manage_user 的登录密码', self.post(f'/admin/users/{uid}/edit', {'action': 'password', 'password': 'NewPass@123', 'confirm_password': 'NewPass@123'}).get_data(as_text=True))
        # 重置后学生可用新密码登录（账号当时为停用态，先启用）
        self.post('/admin/users', {'uid': uid, 'status': 'active'})
        student = self.app.test_client()
        self.client_post(student, '/login', {'username': 'manage_user', 'password': 'NewPass@123'})
        with student.session_transaction() as sess:
            self.assertIn('uid', sess)
        # 有提交与得分记录的账号也能删除，相关记录随账号清理
        with self.app.app_context():
            call('sp_submit_flag', (uid, 1, 'flag{w3lc0me_pwn}'), ('result', 'score', 'message'))
        self.assertIn('已删除', self.post(f'/admin/users/{uid}/edit', {'action': 'delete'}).get_data(as_text=True))
        with self.app.app_context():
            self.assertIsNone(query('SELECT Uid FROM Users WHERE Uid=%s', (uid,), one=True))
            for table in ('Submissions', 'Solves', 'ScoreLogs', 'OperationLogs'):
                self.assertEqual(query(f'SELECT COUNT(*) AS n FROM {table} WHERE Uid=%s', (uid,), one=True)['n'], 0)
        # 管理员账号受保护，不能从用户管理里修改或删除
        self.assertEqual(self.client.get('/admin/users/1/edit').status_code, 302)
        self.assertIn('管理员账号受保护', self.post('/admin/users/1/edit', {'action': 'delete'}).get_data(as_text=True))


if __name__ == '__main__':
    unittest.main(verbosity=2)
