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

    # 功能路由定义于下方，便于按模块阅读与调试。
    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)
