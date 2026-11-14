"""每个请求独立连接，所有值通过参数绑定传入。"""
import os
import pymysql
from flask import g


def connection():
    if 'db' not in g:
        options = dict(host=os.getenv('CTF_DB_HOST', '127.0.0.1'),
                       port=int(os.getenv('CTF_DB_PORT', '3306')),
                       user=os.getenv('CTF_DB_USER', 'ctf_app'),
                       password=os.getenv('CTF_DB_PASSWORD', ''),
                       database=os.getenv('CTF_DB_NAME', 'ctf'),
                       charset='utf8mb4', autocommit=True,
                       cursorclass=pymysql.cursors.DictCursor)
        if os.getenv('CTF_DB_SOCK'):
            options['unix_socket'] = os.environ['CTF_DB_SOCK']
        g.db = pymysql.connect(**options)
    return g.db


def close_db(_error=None):
    db = g.pop('db', None)
    if db:
        db.close()


def query(sql, args=(), one=False):
    with connection().cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchone() if one else cur.fetchall()


def execute(sql, args=()):
    with connection().cursor() as cur:
        cur.execute(sql, args)
        return cur.rowcount


PROCEDURES = {'sp_register_user', 'sp_add_challenge', 'sp_publish_challenge', 'sp_submit_flag'}


def call(name, inputs, outputs):
    # name 和 outputs 由服务端固定，不接受客户端传入的对象名。
    if name not in PROCEDURES or any(x not in {'uid', 'result', 'message', 'chid', 'score'} for x in outputs):
        raise ValueError('未知存储过程或输出参数')
    placeholders = ['%s'] * len(inputs) + ['@out_' + x for x in outputs]
    with connection().cursor() as cur:
        cur.execute('CALL ' + name + '(' + ','.join(placeholders) + ')', inputs)
        while cur.nextset():
            pass
        cur.execute('SELECT ' + ','.join('@out_' + x + ' AS ' + x for x in outputs))
        return cur.fetchone()
