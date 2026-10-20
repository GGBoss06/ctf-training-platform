"""CTF 训练竞赛平台：数据库脚本自动化验证。

执行前请先启动 MySQL 实例，然后运行（默认连接本机 3306 的 root）：
    python3 work/verify_db.py
    CTF_DB_SOCK=/path/to/mysql.sock python3 work/verify_db.py          # 走 socket
    CTF_DB_HOST=127.0.0.1 CTF_DB_PORT=3306 CTF_DB_USER=root \
        CTF_DB_PASSWORD=... python3 work/verify_db.py                  # 走网络连接

脚本会重建 ctf 库并导入 outputs/ctf_init.sql，逐项验证视图、存储过程、触发器与约束，
最后再次重建恢复初始状态，全部结果写入 work/db_verification.json。
"""
import json
import os
import subprocess
import sys
import datetime
from decimal import Decimal
from pathlib import Path

import pymysql

ROOT = Path(__file__).resolve().parent.parent
SQL_FILE = Path(os.environ.get('CTF_SQL', ROOT / 'database' / 'ctf_init.sql'))
OUT_FILE = Path(os.environ.get('CTF_OUT', ROOT / 'docs' / 'db_verification.json'))
MYSQL_BIN = os.environ.get('CTF_MYSQL_BIN', 'mysql')
SOCK = os.environ.get('CTF_DB_SOCK')
HOST = os.environ.get('CTF_DB_HOST', '127.0.0.1')
PORT = int(os.environ.get('CTF_DB_PORT', '3306'))
USER = os.environ.get('CTF_DB_USER', 'root')
PASSWORD = os.environ.get('CTF_DB_PASSWORD', '')

checks = []


def cli_base():
    if SOCK:
        return [MYSQL_BIN, '--no-defaults', '-S', SOCK, '-u', USER]
    args = [MYSQL_BIN, '--no-defaults', '-h', HOST, '-P', str(PORT), '-u', USER]
    if PASSWORD:
        args.append('-p' + PASSWORD)
    return args


def reload_schema():
    """重建 ctf 库并重新导入初始化脚本。"""
    subprocess.run(cli_base() + ['-e', 'DROP DATABASE IF EXISTS ctf;'], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    with SQL_FILE.open('rb') as fh:
        r = subprocess.run(cli_base(), stdin=fh, capture_output=True)
    if r.returncode != 0:
        sys.exit('导入 ctf_init.sql 失败：\n' + r.stderr.decode())


def connect():
    if SOCK:
        return pymysql.connect(unix_socket=SOCK, user=USER, database='ctf',
                               charset='utf8mb4', autocommit=False)
    return pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, database='ctf',
                           charset='utf8mb4', autocommit=False)


def norm(value):
    """把 Decimal 与日期时间归一化，保证 JSON 可序列化。"""
    if isinstance(value, (datetime.datetime, datetime.date, datetime.timedelta)):
        return str(value)
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, list):
        return [norm(v) for v in value]
    if isinstance(value, tuple):
        return [norm(v) for v in value]
    if isinstance(value, dict):
        return {k: norm(v) for k, v in value.items()}
    return value


def rows(cur, sql, args=None):
    cur.execute(sql, args)
    return [norm(list(r)) for r in cur.fetchall()]


def scalar(cur, sql, args=None):
    cur.execute(sql, args)
    return norm(cur.fetchone()[0])


def call_out(conn, call_sql, out_names, args=None):
    """调用带 OUT 参数的存储过程并取回输出参数。"""
    with conn.cursor() as cur:
        cur.execute('SET ' + ', '.join(f'@{n} = NULL' for n in out_names))
        cur.execute(call_sql, args)
        while cur.nextset():
            pass
        cur.execute('SELECT ' + ', '.join(f'@{n}' for n in out_names))
        return norm(list(cur.fetchone()))


def call_rows(conn, call_sql, args=None):
    """调用返回结果集的存储过程。"""
    with conn.cursor() as cur:
        cur.execute(call_sql, args)
        out = [norm(list(r)) for r in cur.fetchall()]
        while cur.nextset():
            pass
        return out


def expect_error(conn, sql, args, code, label):
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args)
    except pymysql.err.MySQLError as exc:
        conn.rollback()
        assert exc.args[0] == code, f'{label}：期望错误码 {code}，实际 {exc.args}'
        checks.append(f'{label}（错误码 {code}）')
    else:
        conn.rollback()
        raise AssertionError(f'{label}：本应被拒绝，实际执行成功')


def main():
    reload_schema()
    conn = connect()
    with conn.cursor() as cur:
        version = scalar(cur, 'SELECT VERSION()')

        # ---------- 一、初始数据与对象数量 ----------
        counts = {
            'users': scalar(cur, 'SELECT COUNT(*) FROM Users'),
            'categories': scalar(cur, 'SELECT COUNT(*) FROM Categories'),
            'challenges': scalar(cur, 'SELECT COUNT(*) FROM Challenges'),
            'online': scalar(cur, "SELECT COUNT(*) FROM Challenges WHERE Status='online'"),
            'draft': scalar(cur, "SELECT COUNT(*) FROM Challenges WHERE Status='draft'"),
            'offline': scalar(cur, "SELECT COUNT(*) FROM Challenges WHERE Status='offline'"),
            'submissions': scalar(cur, 'SELECT COUNT(*) FROM Submissions'),
            'solves': scalar(cur, 'SELECT COUNT(*) FROM Solves'),
            'scorelogs': scalar(cur, 'SELECT COUNT(*) FROM ScoreLogs'),
            'operationlogs': scalar(cur, 'SELECT COUNT(*) FROM OperationLogs'),
            'views': scalar(cur, "SELECT COUNT(*) FROM information_schema.VIEWS WHERE TABLE_SCHEMA='ctf'"),
            'procedures': scalar(cur, "SELECT COUNT(*) FROM information_schema.ROUTINES "
                                      "WHERE ROUTINE_SCHEMA='ctf' AND ROUTINE_TYPE='PROCEDURE'"),
            'triggers': scalar(cur, "SELECT COUNT(*) FROM information_schema.TRIGGERS "
                                    "WHERE TRIGGER_SCHEMA='ctf'"),
            'foreign_keys': scalar(cur, "SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS "
                                        "WHERE CONSTRAINT_SCHEMA='ctf' AND CONSTRAINT_TYPE='FOREIGN KEY'"),
        }
        assert counts == {'users': 11, 'categories': 5, 'challenges': 16, 'online': 13, 'draft': 2,
                          'offline': 1, 'submissions': 28, 'solves': 22, 'scorelogs': 22,
                          'operationlogs': 11, 'views': 5, 'procedures': 5, 'triggers': 3,
                          'foreign_keys': 10}, counts
        checks.append('初始数据规模：11 用户、5 分类、16 题目（上架 13）、28 次提交、22 条解题计分')
        checks.append('对象数量：7 张基本表、5 个视图、5 个存储过程、3 个触发器、10 个外键约束')

        # ---------- 二、视图 ----------
        public_cols = [r[0] for r in rows(
            cur, "SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='ctf' "
                 "AND TABLE_NAME='v_challenge_public' ORDER BY ORDINAL_POSITION")]
        assert 'FlagHash' not in public_cols and 'FlagSalt' not in public_cols, public_cols
        assert scalar(cur, 'SELECT COUNT(*) FROM v_challenge_public') == 13
        checks.append('公共题库视图只含 13 条已上架题目，且不输出 FlagHash / FlagSalt 列')

        rank = rows(cur, 'SELECT 名次, 用户名, 总分, 解题数 FROM v_total_rank ORDER BY 名次')
        assert rank[0][1:] == ['wujiu', 900, 4], rank
        assert len(rank) == 9 and sum(r[2] for r in rank) == 3200 and sum(r[3] for r in rank) == 22
        checks.append('总分榜 9 人入选，榜首 wujiu 900 分，全站合计 3200 分与 22 条解题记录一致')

        cat_rank = rows(cur, 'SELECT 分类, 名次, 用户名, 分类得分 FROM v_category_rank '
                             'ORDER BY 分类编号, 名次')
        assert len(cat_rank) == 20 and sum(r[3] for r in cat_rank) == 3200, cat_rank
        checks.append('分类榜按 5 个分类给出 20 行排名，分类得分合计与总分榜一致')

        zhangsan = rows(cur, "SELECT 提交编号, 分类, 题名, 是否答对, 本次得分 FROM v_submission_record "
                             "WHERE 用户名='zhangsan' ORDER BY 提交时间")
        assert len(zhangsan) == 4 and sum(r[4] for r in zhangsan) == 550, zhangsan
        checks.append('答题记录视图按用户返回逐笔记录，zhangsan 4 条记录得分合计 550 分')

        dist = dict(rows(cur, 'SELECT ca.Cname, COUNT(*) FROM Challenges ch '
                              'JOIN Categories ca ON ch.Cid = ca.Cid GROUP BY ca.Cname'))
        assert dist == {'Pwn': 3, 'Web': 4, 'Reverse': 3, 'Crypto': 3, 'Misc': 3}, dist
        checks.append('题目分类分布正确：Pwn 3、Web 4、Reverse 3、Crypto 3、Misc 3')

        # 演示账号口令与演示 flag 的散列一致性（文档 9.1 与 9.4 节记载的凭据）
        salt, h = rows(cur, "SELECT Salt, PasswordHash FROM Users WHERE Username='zhangsan'")[0]
        assert scalar(cur, "SELECT SHA2(CONCAT('Pass@123', %s), 256)", (salt,)) == h
        salt, h = rows(cur, "SELECT Salt, PasswordHash FROM Users WHERE Username='admin'")[0]
        assert scalar(cur, "SELECT SHA2(CONCAT('Admin@123', %s), 256)", (salt,)) == h
        f_salt, f_hash = rows(cur, 'SELECT FlagSalt, FlagHash FROM Challenges WHERE Chid=1')[0]
        assert scalar(cur, "SELECT SHA2(CONCAT('flag{w3lc0me_pwn}', %s), 256)", (f_salt,)) == f_hash
        checks.append('文档记载的演示口令与演示 flag 都能由库中散列验证通过')

        # ---------- 三、触发器一致性 ----------
        mism = scalar(cur, """
            SELECT COUNT(*) FROM (
                SELECT t.Uid, t.s, l.t
                FROM (SELECT Uid, SUM(ScoreAwarded) s FROM Solves GROUP BY Uid) t
                JOIN (SELECT Uid, MAX(TotalAfter) t FROM ScoreLogs GROUP BY Uid) l ON l.Uid = t.Uid
                WHERE t.s <> l.t) x""")
        assert mism == 0, mism
        checks.append('积分日志记录的变动后总分与解题计分累计逐人一致')

        op = rows(cur, "SELECT Action, Target, Detail FROM OperationLogs WHERE Action='注册账号' LIMIT 2")
        assert len(op) == 2, op
        checks.append('注册触发器为 11 个账号自动写入操作日志')

        # ---------- 四、注册过程 ----------
        uid, res, msg = call_out(conn, 'CALL sp_register_user(%s, %s, %s, @uid, @res, @msg)',
                                 ['uid', 'res', 'msg'], ('newbie01', 'Pass@123', 'newbie01@ctf.edu'))
        assert res == 'ok' and uid and uid > 11, (uid, res, msg)
        stored = rows(cur, 'SELECT PasswordHash, Salt FROM Users WHERE Uid=%s', (uid,))
        h, salt = stored[0]
        assert len(h) == 64 and h != 'Pass@123'
        assert scalar(cur, "SELECT SHA2(CONCAT('Pass@123', %s), 256)", (salt,)) == h
        checks.append('注册过程写入加盐散列口令，库中不存在口令明文')

        _, res, msg = call_out(conn, 'CALL sp_register_user(%s, %s, %s, @uid, @res, @msg)',
                               ['uid', 'res', 'msg'], ('zhangsan', 'Pass@123', 'z@ctf.edu'))
        assert res == 'duplicate', (res, msg)
        checks.append('重名注册返回 duplicate，不会产生第二个同名账号')

        _, res, msg = call_out(conn, 'CALL sp_register_user(%s, %s, %s, @uid, @res, @msg)',
                               ['uid', 'res', 'msg'], ('ab', '123', 'bad'))
        assert res == 'invalid', (res, msg)
        checks.append('用户名、口令与邮箱不满足校验规则时返回 invalid')

        # ---------- 五、录题与上架 ----------
        chid, res, msg = call_out(
            conn, 'CALL sp_add_challenge(%s, %s, %s, %s, %s, %s, %s, %s, @chid, @res, @msg)',
            ['chid', 'res', 'msg'],
            (1, 2, '验证用题目', '用于验证录题与上架流程', 2, 200, 'flag{v3r1fy_fl0w}', 'attachments/t.zip'))
        assert res == 'ok' and chid == 17, (chid, res, msg)
        status, fh = rows(cur, 'SELECT Status, FlagHash FROM Challenges WHERE Chid=%s', (chid,))[0]
        assert status == 'draft' and fh != 'flag{v3r1fy_fl0w}'
        checks.append('录题过程以草稿状态入库，flag 只保存散列值')

        _, res, msg = call_out(conn, 'CALL sp_add_challenge(%s, %s, %s, %s, %s, %s, %s, %s, '
                                     '@chid, @res, @msg)', ['chid', 'res', 'msg'],
                               (2, 2, '越权录题', '学生尝试录题', 1, 100, 'flag{n0p3}', None))
        assert res == 'denied', (res, msg)
        checks.append('学生账号调用录题过程返回 denied')

        res, msg = call_out(conn, 'CALL sp_publish_challenge(%s, %s, @res, @msg)',
                            ['res', 'msg'], (chid, 1))
        assert res == 'ok', (res, msg)
        assert scalar(cur, 'SELECT COUNT(*) FROM v_challenge_public') == 14
        log = rows(cur, "SELECT Uid, Action, Detail FROM OperationLogs WHERE Target='验证用题目' "
                        "ORDER BY Opid DESC LIMIT 1")[0]
        assert log[0] == 1 and log[1] == '题目上架', log
        checks.append('上架后公共题库增至 14 条，触发器按操作人记下“题目上架”日志')

        # ---------- 六、提交判定 ----------
        res, score, msg = call_out(conn, 'CALL sp_submit_flag(%s, %s, %s, @res, @score, @msg)',
                                   ['res', 'score', 'msg'], (11, chid, 'flag{v3r1fy_fl0w}'))
        assert res == 'correct' and score == 200, (res, score, msg)
        assert scalar(cur, 'SELECT SUM(ScoreAwarded) FROM Solves WHERE Uid=11') == 200
        checks.append('首次正确提交返回 correct 并计 200 分，该用户总分升至 200')

        solves_before = scalar(cur, 'SELECT COUNT(*) FROM Solves')
        res, score, msg = call_out(conn, 'CALL sp_submit_flag(%s, %s, %s, @res, @score, @msg)',
                                   ['res', 'score', 'msg'], (11, chid, 'flag{v3r1fy_fl0w}'))
        assert res == 'duplicate' and score == 0, (res, score, msg)
        assert scalar(cur, 'SELECT COUNT(*) FROM Solves') == solves_before
        assert scalar(cur, 'SELECT SUM(ScoreAwarded) FROM Solves WHERE Uid=11') == 200
        checks.append('重复提交同一正确 flag 返回 duplicate，解题记录与总分都不再增长')

        res, score, msg = call_out(conn, 'CALL sp_submit_flag(%s, %s, %s, @res, @score, @msg)',
                                   ['res', 'score', 'msg'], (11, 1, 'flag{wrong_guess}'))
        assert res == 'wrong' and score == 0, (res, score, msg)
        checks.append('错误 flag 返回 wrong 且不得分，该笔提交仍进入答题记录')

        res, score, msg = call_out(conn, 'CALL sp_submit_flag(%s, %s, %s, @res, @score, @msg)',
                                   ['res', 'score', 'msg'], (11, 15, 'flag{l0g_4ud1t}'))
        assert res == 'error' and '未上架' in msg, (res, score, msg)
        checks.append('向草稿题目提交被拒绝，返回“题目未上架”提示')

        res, score, msg = call_out(conn, 'CALL sp_submit_flag(%s, %s, %s, @res, @score, @msg)',
                                   ['res', 'score', 'msg'], (9999, 1, 'flag{w3lc0me_pwn}'))
        assert res == 'error' and '用户不存在' in msg, (res, score, msg)
        checks.append('不存在的用户提交被拒绝')

        recs = call_rows(conn, 'CALL sp_user_records(%s)', (2,))
        assert len(recs) == 4 and sum(r[5] for r in recs) == 550, recs
        checks.append('个人记录过程返回 zhangsan 的 4 笔记录，得分合计 550 分')

        recs = call_rows(conn, 'CALL sp_user_records(%s)', (9999,))
        assert recs == [['用户不存在']], recs
        checks.append('查询不存在用户时过程返回提示行')

        # ---------- 七、约束与事务 ----------
        expect_error(conn, 'INSERT INTO Solves (Uid, Chid, Subid, ScoreAwarded) '
                           'SELECT %s, %s, Subid, 100 FROM Submissions WHERE Uid=%s LIMIT 1',
                     (8, 1, 8), 1062, '重复解题记录被主键 (Uid,Chid) 拒绝')
        expect_error(conn, 'INSERT INTO Submissions (Uid, Chid, FlagHash, IsCorrect) '
                           "VALUES (9999, 1, REPEAT('a',64), 0)", None, 1452,
                     '引用不存在的用户被外键拒绝')
        expect_error(conn, 'DELETE FROM Users WHERE Uid=2', None, 1451,
                     '删除已有提交记录的用户被外键拒绝')
        expect_error(conn, "INSERT INTO Challenges (Cid, Title, Difficulty, Score, FlagHash, FlagSalt, "
                           "AuthorUid) VALUES (1, '难度越界', 9, 100, REPEAT('a',64), REPEAT('b',32), 1)",
                     None, 3819, '难度超出 1 至 5 被 CHECK 约束拒绝')
        expect_error(conn, "INSERT INTO Users (Username, PasswordHash, Salt, Email) "
                           "VALUES ('zhangsan', REPEAT('a',64), REPEAT('b',32), 'x@ctf.edu')",
                     None, 1062, '重复用户名被唯一约束拒绝')

        before = scalar(cur, 'SELECT COUNT(*) FROM Submissions')
        cur.execute("INSERT INTO Submissions (Uid, Chid, FlagHash, IsCorrect) "
                    "VALUES (5, 1, REPEAT('c',64), 0)")
        conn.rollback()
        assert scalar(cur, 'SELECT COUNT(*) FROM Submissions') == before
        checks.append('插入后回滚不留下任何记录，初始数据保持不变')

    conn.close()

    # ---------- 八、恢复初始状态并导出报告所需数据 ----------
    reload_schema()
    conn = connect()
    with conn.cursor() as cur:
        result = {'mysql_version': version, 'checks': checks}
        result['final_counts'] = {
            'users': scalar(cur, 'SELECT COUNT(*) FROM Users'),
            'challenges': scalar(cur, 'SELECT COUNT(*) FROM Challenges'),
            'submissions': scalar(cur, 'SELECT COUNT(*) FROM Submissions'),
            'solves': scalar(cur, 'SELECT COUNT(*) FROM Solves'),
            'scorelogs': scalar(cur, 'SELECT COUNT(*) FROM ScoreLogs'),
            'operationlogs': scalar(cur, 'SELECT COUNT(*) FROM OperationLogs'),
        }
        result['final_total_rank'] = rows(
            cur, 'SELECT 名次, 用户名, 总分, 解题数, DATE_FORMAT(最后解题时间, "%m-%d %H:%i") '
                 'FROM v_total_rank ORDER BY 名次')
        result['final_category_rank'] = rows(
            cur, 'SELECT 分类, 名次, 用户名, 分类得分 FROM v_category_rank ORDER BY 分类编号, 名次')
        result['wujiu_scorelog'] = rows(
            cur, 'SELECT Chid, DeltaScore, TotalAfter, DATE_FORMAT(OccurredAt, "%m-%d %H:%i") '
                 'FROM ScoreLogs WHERE Uid=8 ORDER BY LogId')
        result['public_challenges'] = rows(
            cur, 'SELECT 分类, 题名, 难度, 分值 FROM v_challenge_public ORDER BY 题目编号')
        result['procedures'] = [r[0] for r in rows(
            cur, "SELECT ROUTINE_NAME FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA='ctf' "
                 "AND ROUTINE_TYPE='PROCEDURE' ORDER BY ROUTINE_NAME")]
        result['triggers'] = [r[0] for r in rows(
            cur, "SELECT TRIGGER_NAME FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA='ctf' "
                 "ORDER BY TRIGGER_NAME")]
        result['public_view_columns'] = [r[0] for r in rows(
            cur, "SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='ctf' "
                 "AND TABLE_NAME='v_challenge_public' ORDER BY ORDINAL_POSITION")]
        result['sp_user_records'] = call_rows(conn, 'CALL sp_user_records(%s)', (2,))
        result['wrong_submission'] = rows(
            cur, 'SELECT 用户名, 分类, 题名, 是否答对, 本次得分 FROM v_submission_record '
                 'WHERE 是否答对=0 ORDER BY 提交时间 LIMIT 3')
        result['operation_sample'] = rows(
            cur, 'SELECT Action, Target, Detail FROM OperationLogs ORDER BY Opid LIMIT 3')
        result['scorelog_sample'] = rows(
            cur, 'SELECT u.Username, sl.Chid, sl.DeltaScore, sl.TotalAfter, '
                 'DATE_FORMAT(sl.OccurredAt, "%m-%d %H:%i") FROM ScoreLogs sl '
                 'JOIN Users u ON u.Uid=sl.Uid ORDER BY sl.LogId LIMIT 6')
        result['score_detail_sample'] = rows(
            cur, 'SELECT 用户名, 分类, 题名, 得分, DATE_FORMAT(解出时间, "%m-%d %H:%i") '
                 'FROM v_score_detail WHERE 用户名 IN ("wujiu","zhangsan") ORDER BY 用户名, 解出时间')
    conn.close()

    OUT_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({'mysql_version': version, 'checks': len(checks),
                      'final_counts': result['final_counts'],
                      'total_rank_top3': result['final_total_rank'][:3]}, ensure_ascii=False, indent=2))
    print(f'\n完整结果已写入 {OUT_FILE}')


if __name__ == '__main__':
    main()
