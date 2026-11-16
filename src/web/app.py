"""CTF 训练平台 Web 入口。python src/web/app.py 启动本地演示。"""
import hashlib
import hmac
import os
import re
import secrets
from datetime import timedelta
from functools import wraps
from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
import pymysql
from db import call, close_db, connection, execute, query


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.getenv('CTF_SECRET_KEY') or secrets.token_hex(32),
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                      SESSION_COOKIE_SECURE=os.getenv('CTF_COOKIE_SECURE') == '1',
                      PERMANENT_SESSION_LIFETIME=timedelta(hours=4),
                      MAX_CONTENT_LENGTH=32 * 1024)
    if test_config:
        app.config.update(test_config)
    app.teardown_appcontext(close_db)

    @app.before_request
    def protect_request():
        g.user = None
        if session.get('uid'):
            g.user = query('SELECT Uid,Username,Email,Role,Status FROM Users WHERE Uid=%s',
                           (session['uid'],), one=True)
            if not g.user or g.user['Status'] != 'active':
                session.clear()
                g.user = None
        if request.method == 'POST':
            token = request.form.get('csrf_token', '')
            if not token or not hmac.compare_digest(token.encode(), session.get('csrf_token', '').encode()):
                abort(400, '表单已失效，请刷新后重试')

    def csrf_token():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        return session['csrf_token']

    app.jinja_env.globals['csrf_token'] = csrf_token

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; form-action 'self'; frame-ancestors 'none'"
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(pymysql.MySQLError)
    def database_error(error):
        connection_if_open = g.get('db')
        if connection_if_open:
            connection_if_open.rollback()
        app.logger.error('Database operation failed: %s', type(error).__name__)
        return render_template('error.html', message='数据库暂不可用，请检查连接配置后重试。'), 503

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    def page_error(error):
        return render_template('error.html', message=error.description), error.code

    def require_user(admin=False):
        def decorator(view):
            @wraps(view)
            def wrapper(*args, **kwargs):
                if not g.user:
                    return redirect(url_for('login'))
                if admin and g.user['Role'] != 'admin':
                    abort(403, '此功能仅对管理员开放')
                return view(*args, **kwargs)
            return wrapper
        return decorator

    @app.get('/')
    def index():
        return redirect(url_for('challenges'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            email = request.form.get('email', '').strip()
            if not re.fullmatch(r'[A-Za-z0-9_]{3,32}', username) or not 6 <= len(password) <= 64 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email) or len(email) > 64:
                flash('请填写有效的用户名、6 至 64 位密码和邮箱。', 'error')
            else:
                result = call('sp_register_user', (username, password, email), ('uid', 'result', 'message'))
                flash(result['message'], 'success' if result['result'] == 'ok' else 'error')
                if result['result'] == 'ok':
                    return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            user = query('SELECT * FROM Users WHERE Username=%s', (username,), one=True)
            hashed = hashlib.sha256((password + (user['Salt'] if user else '0' * 32)).encode()).hexdigest()
            if user and len(password) <= 64 and hmac.compare_digest(hashed, user['PasswordHash']) and user['Status'] == 'active':
                session.clear()
                session['uid'] = user['Uid']
                session.permanent = True
                return redirect(url_for('challenges'))
            flash('用户名、密码不正确，或账号已停用。', 'error')
        return render_template('login.html')

    @app.post('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.route('/profile', methods=['GET', 'POST'])
    @require_user()
    def profile():
        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            password = request.form.get('new_password', '')
            if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email) or len(email) > 64:
                flash('邮箱格式不正确。', 'error')
            elif password and not 6 <= len(password) <= 64:
                flash('新密码长度应为 6 至 64 位。', 'error')
            elif password:
                stored = query('SELECT PasswordHash,Salt FROM Users WHERE Uid=%s', (g.user['Uid'],), one=True)
                old_hash = hashlib.sha256((request.form.get('current_password', '') + stored['Salt']).encode()).hexdigest()
                if not hmac.compare_digest(old_hash, stored['PasswordHash']):
                    flash('当前密码不正确。', 'error')
                else:
                    salt = secrets.token_hex(16)
                    digest = hashlib.sha256((password + salt).encode()).hexdigest()
                    execute('UPDATE Users SET Email=%s,PasswordHash=%s,Salt=%s WHERE Uid=%s', (email, digest, salt, g.user['Uid']))
                    session.clear()
                    flash('密码已修改，请重新登录。', 'success')
                    return redirect(url_for('login'))
            else:
                execute('UPDATE Users SET Email=%s WHERE Uid=%s', (email, g.user['Uid']))
                flash('个人资料已保存。', 'success')
            return redirect(url_for('profile'))
        records = query('SELECT * FROM v_submission_record WHERE 用户编号=%s ORDER BY 提交编号 DESC LIMIT 100', (g.user['Uid'],))
        scores = query('SELECT * FROM v_score_detail WHERE 用户编号=%s ORDER BY 解出时间 DESC', (g.user['Uid'],))
        return render_template('profile.html', records=records, scores=scores,
                               total=sum(x['得分'] for x in scores))

    @app.get('/challenges')
    def challenges():
        category = request.args.get('category', '').strip()
        difficulty = request.args.get('difficulty', '')
        keyword = request.args.get('q', '').strip()[:64]
        if difficulty and difficulty not in {'1', '2', '3', '4', '5'}:
            abort(400, '难度取值应为 1 至 5')
        rows = query('SELECT * FROM v_challenge_public WHERE (%s="" OR 分类=%s) '
                     'AND (%s="" OR 难度=%s) AND (%s="" OR 题名 LIKE %s) ORDER BY 题目编号',
                     (category, category, difficulty, difficulty or 0, keyword, '%' + keyword + '%'))
        return render_template('challenges.html', rows=rows,
                               categories=query('SELECT * FROM Categories ORDER BY Cid'))

    @app.route('/challenges/<int:chid>', methods=['GET', 'POST'])
    def detail(chid):
        item = query('SELECT * FROM v_challenge_public WHERE 题目编号=%s', (chid,), one=True)
        if not item:
            abort(404, '该题目不存在或尚未上架')
        if request.method == 'POST':
            if not g.user:
                return redirect(url_for('login'))
            flag = request.form.get('flag', '').strip()
            if not 6 <= len(flag) <= 128:
                flash('flag 长度应为 6 至 128 位。', 'error')
            else:
                result = call('sp_submit_flag', (g.user['Uid'], chid, flag), ('result', 'score', 'message'))
                flash(result['message'], 'success' if result['result'] in {'correct', 'duplicate'} else 'error')
            return redirect(url_for('detail', chid=chid))
        solved = g.user and query('SELECT 1 FROM Solves WHERE Uid=%s AND Chid=%s',
                                  (g.user['Uid'], chid), one=True)
        return render_template('detail.html', item=item, solved=solved)

    @app.get('/ranking')
    def ranking():
        category = request.args.get('category', '').strip()
        if category:
            rows = query('SELECT 名次,用户名,分类得分 AS 总分,解题数 FROM v_category_rank WHERE 分类=%s ORDER BY 名次,用户名', (category,))
        else:
            rows = query('SELECT * FROM v_total_rank ORDER BY 名次,用户名')
        return render_template('ranking.html', rows=rows,
                               categories=query('SELECT * FROM Categories ORDER BY Cid'))

    def challenge_values():
        try:
            cid = int(request.form.get('cid', 0))
            difficulty = int(request.form.get('difficulty', 0))
            score = int(request.form.get('score', 0))
        except ValueError:
            abort(400, '分类、难度和分值应为整数')
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        flag = request.form.get('flag', '').strip()
        attachment = request.form.get('attachment', '').strip()
        if not 1 <= difficulty <= 5 or not 1 <= score <= 100000 or not 1 <= len(title) <= 64 or len(description) > 500 or len(attachment) > 128 or (flag and not 6 <= len(flag) <= 128):
            abort(400, '请检查题名、难度、分值、题面及 flag 长度')
        if not query('SELECT 1 FROM Categories WHERE Cid=%s', (cid,), one=True):
            abort(400, '分类不存在')
        return cid, title, description, difficulty, score, flag, attachment

    @app.get('/admin/challenges')
    @require_user(admin=True)
    def admin_challenges():
        rows = query('SELECT ch.Chid,ch.Title,ch.Difficulty,ch.Score,ch.Status,ca.Cname '
                     'FROM Challenges ch JOIN Categories ca ON ca.Cid=ch.Cid ORDER BY ch.Chid DESC')
        return render_template('admin_challenges.html', rows=rows)

    @app.route('/admin/challenges/new', methods=['GET', 'POST'])
    @require_user(admin=True)
    def add_challenge():
        if request.method == 'POST':
            values = challenge_values()
            if not values[5]:
                abort(400, '新建题目必须填写 flag')
            result = call('sp_add_challenge', (g.user['Uid'],) + values, ('chid', 'result', 'message'))
            flash(result['message'], 'success' if result['result'] == 'ok' else 'error')
            return redirect(url_for('admin_challenges'))
        return render_template('challenge_form.html', item=None,
                               categories=query('SELECT * FROM Categories ORDER BY Cid'))

    @app.route('/admin/challenges/<int:chid>/edit', methods=['GET', 'POST'])
    @require_user(admin=True)
    def edit_challenge(chid):
        item = query('SELECT Chid,Cid,Title,Description,Difficulty,Score,Attachment,Status FROM Challenges WHERE Chid=%s', (chid,), one=True)
        if not item:
            abort(404, '题目不存在')
        if request.method == 'POST':
            cid, title, description, difficulty, score, flag, attachment = challenge_values()
            db = connection()
            db.begin()
            try:
                query('SELECT Chid FROM Challenges WHERE Chid=%s FOR UPDATE', (chid,), one=True)
                submitted = query('SELECT 1 FROM Submissions WHERE Chid=%s LIMIT 1', (chid,), one=True)
                if submitted and (flag or cid != item['Cid'] or title != item['Title'] or score != item['Score']):
                    db.rollback()
                    flash('已有提交的题目不能修改 flag、题名、分类或分值。', 'error')
                    return redirect(url_for('edit_challenge', chid=chid))
                execute('UPDATE Challenges SET Cid=%s,Title=%s,Description=%s,Difficulty=%s,Score=%s,Attachment=%s WHERE Chid=%s',
                        (cid, title, description, difficulty, score, attachment, chid))
                if flag:
                    salt = secrets.token_hex(16)
                    digest = hashlib.sha256((flag + salt).encode()).hexdigest()
                    execute('UPDATE Challenges SET FlagHash=%s,FlagSalt=%s WHERE Chid=%s', (digest, salt, chid))
                execute('INSERT INTO OperationLogs(Uid,Action,Target,Detail) VALUES(%s,%s,%s,%s)',
                        (g.user['Uid'], '修改题目', title, '更新题目内容'))
                db.commit()
            except Exception:
                db.rollback()
                raise
            flash('题目信息已更新。', 'success')
            return redirect(url_for('admin_challenges'))
        return render_template('challenge_form.html', item=item,
                               categories=query('SELECT * FROM Categories ORDER BY Cid'))

    @app.post('/admin/challenges/<int:chid>/<action>')
    @require_user(admin=True)
    def challenge_action(chid, action):
        if action == 'publish':
            result = call('sp_publish_challenge', (chid, g.user['Uid']), ('result', 'message'))
            flash(result['message'], 'success' if result['result'] in {'ok', 'noop'} else 'error')
            return redirect(url_for('admin_challenges'))
        if action not in {'offline', 'delete'}:
            abort(404)
        db = connection()
        db.begin()
        try:
            item = query('SELECT Chid,Title,Status FROM Challenges WHERE Chid=%s FOR UPDATE', (chid,), one=True)
            if not item:
                abort(404, '题目不存在')
            submissions = solves = 0
            if action == 'delete':
                # 管理员可删除任意状态的题目。外键在结构层阻止直接删除，
                # 因此先按依赖顺序清理该题目的得分、解题与提交记录，再删题目本身。
                submissions = query('SELECT COUNT(*) AS n FROM Submissions WHERE Chid=%s', (chid,), one=True)['n']
                solves = query('SELECT COUNT(*) AS n FROM Solves WHERE Chid=%s', (chid,), one=True)['n']
                execute('DELETE FROM ScoreLogs WHERE Chid=%s', (chid,))
                execute('DELETE FROM Solves WHERE Chid=%s', (chid,))
                execute('DELETE FROM Submissions WHERE Chid=%s', (chid,))
                execute('DELETE FROM Challenges WHERE Chid=%s', (chid,))
                detail = '删除%s题目，清理 %d 条提交、%d 条得分记录' % (
                    {'draft': '草稿', 'online': '上架', 'offline': '下线'}.get(item['Status'], ''), submissions, solves)
                execute('INSERT INTO OperationLogs(Uid,Action,Target,Detail) VALUES(%s,%s,%s,%s)',
                        (g.user['Uid'], '删除题目', item['Title'], detail))
            else:
                execute('SET @operator_uid=%s', (g.user['Uid'],))
                execute("UPDATE Challenges SET Status='offline' WHERE Chid=%s", (chid,))
            db.commit()
        except Exception:
            db.rollback()
            raise
        if action == 'delete':
            if submissions or solves:
                flash('题目已删除，同时清理了 %d 条提交记录和 %d 条得分记录。' % (submissions, solves), 'success')
            else:
                flash('题目已删除。', 'success')
        else:
            flash('题目已下线。', 'success')
        return redirect(url_for('admin_challenges'))

    @app.route('/admin/users', methods=['GET', 'POST'])
    @require_user(admin=True)
    def admin_users():
        if request.method == 'POST':
            try:
                uid = int(request.form.get('uid', 0))
            except ValueError:
                abort(400, '用户编号无效')
            status = request.form.get('status')
            if status not in {'active', 'disabled'}:
                abort(400, '账号状态无效')
            changed = execute("UPDATE Users SET Status=%s WHERE Uid=%s AND Role='student'", (status, uid))
            flash('学生账号状态已更新。' if changed else '未更新，管理员账号受保护。', 'success' if changed else 'error')
            return redirect(url_for('admin_users'))
        keyword = request.args.get('q', '').strip()[:32]
        users = query('SELECT u.Uid,u.Username,u.Email,u.Role,u.Status,'
                      '(SELECT COUNT(*) FROM Submissions s WHERE s.Uid=u.Uid) AS SubmissionCount,'
                      '(SELECT COUNT(*) FROM Solves so WHERE so.Uid=u.Uid) AS SolveCount,'
                      '(SELECT COALESCE(SUM(so.ScoreAwarded),0) FROM Solves so WHERE so.Uid=u.Uid) AS TotalScore '
                      'FROM Users u WHERE u.Username LIKE %s ORDER BY u.Uid', ('%' + keyword + '%',))
        return render_template('users.html', users=users)

    @app.route('/admin/users/<int:uid>/edit', methods=['GET', 'POST'])
    @require_user(admin=True)
    def admin_user_edit(uid):
        target = query('SELECT Uid,Username,Email,Role,Status,CreatedAt FROM Users WHERE Uid=%s', (uid,), one=True)
        if not target:
            abort(404, '用户不存在')
        if target['Role'] != 'student':
            flash('管理员账号受保护，不能在用户管理中修改。', 'error')
            return redirect(url_for('admin_users'))
        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'password':
                password = request.form.get('password', '')
                confirm = request.form.get('confirm_password', '')
                if not 6 <= len(password) <= 64:
                    flash('新密码长度应为 6 至 64 位。', 'error')
                elif password != confirm:
                    flash('两次输入的新密码不一致。', 'error')
                else:
                    salt = secrets.token_hex(16)
                    digest = hashlib.sha256((password + salt).encode()).hexdigest()
                    execute("UPDATE Users SET PasswordHash=%s,Salt=%s WHERE Uid=%s AND Role='student'", (digest, salt, uid))
                    execute('INSERT INTO OperationLogs(Uid,Action,Target,Detail) VALUES(%s,%s,%s,%s)',
                            (g.user['Uid'], '重置密码', target['Username'], '管理员重置学生登录口令'))
                    flash('已重置 %s 的登录密码（口令哈希后入库，明文不保存）。' % target['Username'], 'success')
                return redirect(url_for('admin_user_edit', uid=uid))
            if action == 'delete':
                db = connection()
                db.begin()
                try:
                    locked = query("SELECT Uid,Username FROM Users WHERE Uid=%s AND Role='student' FOR UPDATE", (uid,), one=True)
                    if not locked:
                        abort(404, '用户不存在或受保护')
                    submissions = query('SELECT COUNT(*) AS n FROM Submissions WHERE Uid=%s', (uid,), one=True)['n']
                    solves = query('SELECT COUNT(*) AS n FROM Solves WHERE Uid=%s', (uid,), one=True)['n']
                    # 外键要求先清理引用该账号的得分、解题、提交与操作日志，再删除账号本身。
                    execute('DELETE FROM ScoreLogs WHERE Uid=%s', (uid,))
                    execute('DELETE FROM Solves WHERE Uid=%s', (uid,))
                    execute('DELETE FROM Submissions WHERE Uid=%s', (uid,))
                    execute('DELETE FROM OperationLogs WHERE Uid=%s', (uid,))
                    execute('DELETE FROM Users WHERE Uid=%s', (uid,))
                    execute('INSERT INTO OperationLogs(Uid,Action,Target,Detail) VALUES(%s,%s,%s,%s)',
                            (g.user['Uid'], '删除账号', locked['Username'],
                             '删除学生账号，清理 %d 条提交、%d 条得分记录' % (submissions, solves)))
                    db.commit()
                except Exception:
                    db.rollback()
                    raise
                flash('账号 %s 及其提交记录已删除。' % locked['Username'], 'success')
                return redirect(url_for('admin_users'))
            email = request.form.get('email', '').strip()
            status = request.form.get('status')
            if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email) or len(email) > 64:
                flash('邮箱格式不正确。', 'error')
            elif status not in {'active', 'disabled'}:
                flash('账号状态无效。', 'error')
            else:
                execute("UPDATE Users SET Email=%s,Status=%s WHERE Uid=%s AND Role='student'", (email, status, uid))
                execute('INSERT INTO OperationLogs(Uid,Action,Target,Detail) VALUES(%s,%s,%s,%s)',
                        (g.user['Uid'], '修改账号', target['Username'], '更新学生邮箱或账号状态'))
                flash('账号资料已更新。', 'success')
            return redirect(url_for('admin_user_edit', uid=uid))
        stats = dict(
            submissions=query('SELECT COUNT(*) AS n FROM Submissions WHERE Uid=%s', (uid,), one=True)['n'],
            solves=query('SELECT COUNT(*) AS n FROM Solves WHERE Uid=%s', (uid,), one=True)['n'],
            score=query('SELECT COALESCE(SUM(ScoreAwarded),0) AS n FROM Solves WHERE Uid=%s', (uid,), one=True)['n'],
            logs=query('SELECT COUNT(*) AS n FROM OperationLogs WHERE Uid=%s', (uid,), one=True)['n'])
        records = query('SELECT * FROM v_submission_record WHERE 用户编号=%s ORDER BY 提交编号 DESC LIMIT 20', (uid,))
        return render_template('admin_user_edit.html', target=target, stats=stats, records=records)

    @app.get('/admin/logs')
    @require_user(admin=True)
    def admin_logs():
        keyword = request.args.get('q', '').strip()[:32]
        day = request.args.get('day', '')
        if day:
            from datetime import date
            try:
                date.fromisoformat(day)
            except ValueError:
                abort(400, '日期格式不正确')
        logs = query('SELECT o.*,u.Username FROM OperationLogs o JOIN Users u ON u.Uid=o.Uid '
                     'WHERE (%s="" OR u.Username LIKE %s) AND (%s="" OR DATE(o.OccurredAt)=%s) ORDER BY Opid DESC LIMIT 100',
                     (keyword, '%' + keyword + '%', day, day or '2000-01-01'))
        scores = query('SELECT s.*,u.Username FROM ScoreLogs s JOIN Users u ON u.Uid=s.Uid '
                       'WHERE (%s="" OR u.Username LIKE %s) AND (%s="" OR DATE(s.OccurredAt)=%s) ORDER BY LogId DESC LIMIT 100',
                       (keyword, '%' + keyword + '%', day, day or '2000-01-01'))
        return render_template('logs.html', logs=logs, scores=scores)
    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)
