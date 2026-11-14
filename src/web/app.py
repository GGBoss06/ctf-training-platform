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
            if not token or not hmac.compare_digest(token, session.get('csrf_token', '')):
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

    # 训练与管理路由。
    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)
