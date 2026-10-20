"""生成《CTF训练竞赛平台数据库实现说明.docx》。

数据来源：outputs/ctf_init.sql（代码段）与 work/db_verification.json（实测结果）。
运行：python3 work/build_report.py
"""
from pathlib import Path
import json
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

OUT = Path('docs')
sql = Path('database/ctf_init.sql').read_text()
v = json.loads(Path('docs/db_verification.json').read_text())
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(1.9)
sec.left_margin = sec.right_margin = Cm(2)
sec.footer_distance = Cm(.9)


def font_style(style, western, east, size, bold=False):
    s = doc.styles[style]
    s.font.name = western
    s.font.size = Pt(size)
    s.font.bold = bold
    s.font.color.rgb = RGBColor(0, 0, 0)
    rp = s.element.get_or_add_rPr()
    for key in list(rp.rFonts.attrib):
        if 'theme' in key.lower():
            del rp.rFonts.attrib[key]
    rp.rFonts.set(qn('w:eastAsia'), east)
    rp.rFonts.set(qn('w:cs'), east)
    sz = rp.find(qn('w:szCs'))
    if sz is None:
        sz = OxmlElement('w:szCs'); rp.append(sz)
    sz.set(qn('w:val'), str(int(size * 2)))
    bc = rp.find(qn('w:bCs'))
    if bc is None:
        bc = OxmlElement('w:bCs'); rp.append(bc)
    bc.set(qn('w:val'), '1' if bold else '0')
    return s


n = font_style('Normal', 'Calibri', 'Songti SC', 10.5)
n.paragraph_format.line_spacing = Pt(16)
n.paragraph_format.space_after = Pt(6)
font_style('Title', 'Calibri', 'Songti SC', 23, True)
for style in doc.styles:
    for border in list(style.element.iter(qn('w:pBdr'))):
        border.getparent().remove(border)
for name, size in [('Heading 1', 16), ('Heading 2', 12)]:
    h = font_style(name, 'Calibri', 'Songti SC', size, True)
    h.paragraph_format.space_before = Pt(9)
    h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.keep_with_next = True
cs = doc.styles.add_style('CodeBlock', 1)
cs.font.name = 'Courier New'
cs.font.size = Pt(8.5)
cs.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), 'Songti SC')
cs.paragraph_format.line_spacing = Pt(11)
cs.paragraph_format.space_after = Pt(0)
cs.paragraph_format.space_before = Pt(0)
cs.paragraph_format.left_indent = Cm(.15)
cs.paragraph_format.widow_control = False
for style in doc.styles:
    if style.type == 1:
        snap = OxmlElement('w:snapToGrid')
        snap.set(qn('w:val'), '0')
        style.element.get_or_add_pPr().append(snap)

foot = sec.footer.paragraphs[0]
foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
foot.add_run('第 ')
f = OxmlElement('w:fldSimple'); f.set(qn('w:instr'), 'PAGE'); foot._p.append(f)
foot.add_run(' 页')
for r in foot.runs:
    r.font.size = Pt(9)


def p(text):
    return doc.add_paragraph(text)


def h(text, level=1):
    return doc.add_heading(text, level)


def page(title):
    """章节标题。正文连续排版，标题带 keep_with_next，避免出现整页空白。"""
    h(title)


def code(text):
    for line in text.strip().splitlines():
        doc.add_paragraph(line, 'CodeBlock')
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def table(headers, rows, widths, center_cols=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for c, width in zip(t.columns, widths):
        c.width = Cm(width)
    for i, val in enumerate(headers):
        t.rows[0].cells[i].text = val
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)
    pr = t._tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        e = OxmlElement('w:' + edge)
        for k, val in [('val', 'single'), ('sz', '4'), ('color', 'D9D9D9')]:
            e.set(qn('w:' + k), val)
        borders.append(e)
    pr.append(borders)
    center = center_cols if center_cols is not None else list(range(len(headers)))
    if headers == TABLE_H:
        center = [1, 2, 3]
    for ri, row in enumerate(t.rows):
        trpr = row._tr.get_or_add_trPr()
        trpr.append(OxmlElement('w:cantSplit'))
        if ri == 0:
            trpr.append(OxmlElement('w:tblHeader'))
        for ci, cell in enumerate(row.cells):
            cell.width = Cm(widths[ci])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cp = cell._tc.get_or_add_tcPr()
            mar = OxmlElement('w:tcMar')
            for edge, value in [('top', '70'), ('bottom', '70'), ('left', '90'), ('right', '90')]:
                e = OxmlElement('w:' + edge); e.set(qn('w:w'), value); e.set(qn('w:type'), 'dxa')
                mar.append(e)
            cp.append(mar)
            if ri == 0:
                sh = OxmlElement('w:shd'); sh.set(qn('w:fill'), 'DBE7F2'); cp.append(sh)
            for para in cell.paragraphs:
                para.paragraph_format.space_after = Pt(0)
                para.paragraph_format.line_spacing = Pt(13)
                if ri > 0 and ci in center:
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:
                    run.font.size = Pt(9.5)
                    if ri == 0:
                        run.bold = True
    p('').paragraph_format.space_after = Pt(0)
    return t


def cut(start, end):
    i = sql.index(start)
    j = sql.index(end, i)
    block = sql[i:j].rstrip()
    lines = block.splitlines()
    while lines and lines[-1].startswith('-- ---'):
        lines.pop()
        while lines and not lines[-1].strip():
            lines.pop()
    return '\n'.join(lines)


TABLE_H = ['字段名', '数据类型', '允许空值', '键与约束', '字段说明']
TABLE_W = [3.6, 2.7, 1.8, 3, 5.9]

doc.add_paragraph('CTF 训练竞赛平台\n数据库设计与实现', 'Title')
p('大作业题目：CTF训练竞赛平台的设计与实现')
p('常态化训练要求学生在任意时间登录作答，flag 判定与得分统计一旦依赖人工核对，就会出现反馈慢、重复提交难以查重、'
  '排行榜与明细对不上等问题。本设计把判定与计分下沉到数据库：题目、提交、解题计分分别建表，flag 与口令在库中只保存加盐散列；'
  '重复提交由解题表主键 (Uid, Chid) 在结构层拦下；比对、计分与留痕由存储过程 sp_submit_flag 在同一事务内完成；'
  '公共题库、个人答题记录与总分榜、分类榜由 5 个视图直接输出，应用层只需参数化调用。'
  '脚本已在 MySQL ' + v['mysql_version'] + ' 实例上完整执行，' + str(len(v['checks'])) + ' 项验证全部通过，结果见第九节。')

h('一  系统功能与实现环境')
p('平台服务参赛学生与训练管理员两类角色。学生注册登录后进入前台训练子系统，按分类（Pwn/Web/Reverse/Crypto/Misc）'
  '与难度检索题目、查看题目详情，在题目详情页提交 flag 并立即得到判定结果与本次得分；在个人中心可查看逐笔答题记录与得分明细。'
  '管理员负责录入题目与上架，题目上架后进入公共题库供全体学生作答。系统通过总分榜与分类榜实时展示训练排名，'
  '并由触发器自动记录积分变动、账号注册与题目上架等关键操作。')
table(['项目', '实现内容'], [
    ['数据库', 'ctf，字符集 utf8mb4，存储引擎 InnoDB'],
    ['运行环境', 'MySQL 8.0+；本次在 MySQL ' + v['mysql_version'] + ' 上完成执行与验证'],
    ['基本表', 'Users、Categories、Challenges、Submissions、Solves、ScoreLogs、OperationLogs，共 7 张'],
    ['视图', 'v_challenge_public、v_submission_record、v_score_detail、v_total_rank、v_category_rank，共 5 个'],
    ['存储过程', '注册、录题、上架、flag 判定、个人记录，共 5 个'],
    ['触发器', '注册留痕、题目状态变更留痕、积分变动留痕，共 3 个'],
    ['初始数据', '11 个账号、5 个分类、16 道题目（上架 13）、28 次提交、22 条解题计分'],
], [3.2, 13.8], center_cols=[])

h('二  数据库关系设计')
p('Users 是全局主体表：管理员通过 AuthorUid 关联题目，学生通过 Uid 关联提交记录与解题计分。'
  'Categories 与 Challenges 是一对多关系，每道题目归属一个方向分类。'
  'Challenges 与 Submissions 是一对多关系，一道题目可以收到多次提交，每次提交都留档。'
  '解题计分表 Solves 以 (Uid, Chid) 为联合主键，把“同一学生同一题目只计分一次”固化为结构约束；'
  'Solves.Subid 指向首次正确提交，使每笔得分都能追溯到具体那一次提交。'
  'ScoreLogs 与 OperationLogs 分别记录积分变动与管理操作，由触发器在数据写入时自动补全。')
code('Users.Uid        1 —— N  Challenges.AuthorUid      管理员录题\n'
     'Categories.Cid   1 —— N  Challenges.Cid            分类收录题目\n'
     'Users.Uid        1 —— N  Submissions.Uid           学生提交 flag\n'
     'Challenges.Chid  1 —— N  Submissions.Chid          题目接收提交\n'
     'Users.Uid + Challenges.Chid  —— 1  Solves          联合主键保证只计分一次\n'
     'Submissions.Subid 1 —— 1  Solves.Subid             得分追溯到首次正确提交')

page('三  表结构设计')
p('下表中的“允许空值”指字段是否可为 NULL。主键编号采用自增整数，新增记录时无需显式填写；'
  '口令与 flag 一律以加盐散列保存，库中不存在可用于直接比对的明文。')

h('3.1  用户表 Users', 2)
p('保存登录凭据与角色，学生与管理员共用一张表，以 Role 区分权限。')
table(TABLE_H, [
    ['Uid', 'INT', '否', '主键 自增', '用户编号'],
    ['Username', 'VARCHAR(32)', '否', '唯一 NOT NULL', '登录名，全局唯一'],
    ['PasswordHash', 'CHAR(64)', '否', 'NOT NULL', '口令散列 SHA2(口令+盐,256)'],
    ['Salt', 'CHAR(32)', '否', 'NOT NULL', '口令盐'],
    ['Email', 'VARCHAR(64)', '否', 'NOT NULL', '电子邮箱'],
    ['Role', 'ENUM', '否', '默认 student', '角色 student 或 admin'],
    ['Status', 'ENUM', '否', '默认 active', '账号状态 active 或 disabled'],
    ['CreatedAt', 'DATETIME', '否', '默认当前时间', '注册时间'],
], TABLE_W)

h('3.2  题目分类表 Categories', 2)
p('五个训练方向各占一行，检索条件与分类榜都以此为基准。')
table(TABLE_H, [
    ['Cid', 'INT', '否', '主键 自增', '分类编号'],
    ['Cname', 'VARCHAR(16)', '否', '唯一 NOT NULL', '分类名称 Pwn/Web/Reverse/Crypto/Misc'],
    ['Cdesc', 'VARCHAR(100)', '是', '无', '分类说明'],
], TABLE_W)

h('3.3  题目表 Challenges', 2)
p('保存题面、难度、分值与 flag 散列，用 Status 三态控制题目是否进入公共题库。')
table(TABLE_H, [
    ['Chid', 'INT', '否', '主键 自增', '题目编号'],
    ['Cid', 'INT', '否', '外键 NOT NULL', '引用 Categories(Cid)'],
    ['Title', 'VARCHAR(64)', '否', 'NOT NULL', '题名'],
    ['Description', 'VARCHAR(500)', '是', '无', '题目描述'],
    ['Difficulty', 'TINYINT', '否', 'CHECK 1 至 5', '难度'],
    ['Score', 'INT', '否', 'CHECK 大于 0', '基础分值'],
    ['FlagHash', 'CHAR(64)', '否', 'NOT NULL', 'flag 散列 SHA2(flag+盐,256)'],
    ['FlagSalt', 'CHAR(32)', '否', 'NOT NULL', 'flag 盐'],
    ['Attachment', 'VARCHAR(128)', '是', '无', '附件路径'],
    ['Status', 'ENUM', '否', '默认 draft', '上架状态 draft/online/offline'],
    ['AuthorUid', 'INT', '否', '外键 NOT NULL', '引用 Users(Uid)'],
    ['CreatedAt', 'DATETIME', '否', '默认当前时间', '录入时间'],
    ['PublishedAt', 'DATETIME', '是', '无', '上架时间'],
], TABLE_W)

h('3.4  提交记录表 Submissions', 2)
p('每一次 flag 提交都写入一行，正确的与错误的同样留档，个人中心的答题记录与错误次数统计都取自这张表。')
table(TABLE_H, [
    ['Subid', 'BIGINT', '否', '主键 自增', '提交编号'],
    ['Uid', 'INT', '否', '外键 NOT NULL', '引用 Users(Uid)'],
    ['Chid', 'INT', '否', '外键 NOT NULL', '引用 Challenges(Chid)'],
    ['FlagHash', 'CHAR(64)', '否', 'NOT NULL', '本次提交 flag 的散列'],
    ['IsCorrect', 'TINYINT', '否', 'CHECK 取值 0 或 1', '是否正确'],
    ['SubmittedAt', 'DATETIME', '否', '默认当前时间', '提交时间'],
], TABLE_W)

h('3.5  解题计分表 Solves', 2)
p('联合主键 (Uid, Chid) 使重复计分在入库阶段即被拒绝，这是查重与防刷分的主要机制；Subid 让每笔得分可追溯到首次正确提交。')
table(TABLE_H, [
    ['Uid', 'INT', '否', '联合主键', '解题人'],
    ['Chid', 'INT', '否', '联合主键', '题目编号'],
    ['Subid', 'BIGINT', '否', '唯一 外键 NOT NULL', '首次正确提交编号'],
    ['ScoreAwarded', 'INT', '否', 'CHECK 大于 0', '本次得分'],
    ['SolvedAt', 'DATETIME', '否', '默认当前时间', '解出时间'],
], TABLE_W)

h('3.6  积分变动日志 ScoreLogs', 2)
p('每次计分由触发器写入一行，同时保存本次变动与变动后的累计总分，使排名变化可回溯、可核对。')
table(TABLE_H, [
    ['LogId', 'BIGINT', '否', '主键 自增', '日志编号'],
    ['Uid', 'INT', '否', '外键 NOT NULL', '得分人'],
    ['Chid', 'INT', '否', '外键 NOT NULL', '题目编号'],
    ['DeltaScore', 'INT', '否', 'NOT NULL', '本次得分变动'],
    ['TotalAfter', 'INT', '否', 'NOT NULL', '变动后累计总分'],
    ['Action', 'VARCHAR(16)', '否', '默认 solve', '动作类型'],
    ['OccurredAt', 'DATETIME', '否', '默认当前时间', '发生时间'],
], TABLE_W)

h('3.7  管理操作日志 OperationLogs', 2)
p('注册、录题与题目状态变更等关键操作自动留痕，记录操作人、对象与说明。')
table(TABLE_H, [
    ['Opid', 'BIGINT', '否', '主键 自增', '日志编号'],
    ['Uid', 'INT', '否', '外键 NOT NULL', '操作人'],
    ['Action', 'VARCHAR(32)', '否', 'NOT NULL', '操作类型'],
    ['Target', 'VARCHAR(64)', '是', '无', '操作对象'],
    ['Detail', 'VARCHAR(200)', '是', '无', '操作说明'],
    ['OccurredAt', 'DATETIME', '否', '默认当前时间', '发生时间'],
], TABLE_W)

h('3.8  数据完整性与索引', 2)
p('主键与唯一约束覆盖编号、登录名与提交编号；10 个外键把题目、提交、计分与日志全部挂到 Users 与 Categories 上，'
  '引用不存在的用户或题目会被数据库直接拒绝。CHECK 约束限制难度取值 1 至 5、分值大于 0、得分大于 0。'
  'Challenges 上的 (Cid, Difficulty, Status) 复合索引服务分类与难度检索，Submissions 上的 (Uid, SubmittedAt) '
  '索引服务个人答题记录，Solves 与 ScoreLogs 按用户建索引服务排行榜与积分明细查询。')
p('外键采用默认的 RESTRICT 语义，把引用完整性交给数据库保证：只要学生还有提交或计分记录，直接删除账号就会被拒绝；'
  '同样，被提交过的题目也无法被删除。需要下线题目时改用 Status 状态流转，历史提交与得分保持完整。')

page('四  数据库与表的实现代码')
p('脚本先建库，再按 Categories、Users、Challenges、Submissions、Solves、ScoreLogs、OperationLogs 的顺序建表，'
  '保证每个外键引用的父表都已存在。以下代码与配套脚本 outputs/ctf_init.sql 的表结构完全一致。')
p('每张表都显式声明 ENGINE=InnoDB 与 utf8mb4：InnoDB 提供外键、事务与行级锁，utf8mb4 用于保存中文题面与选项。'
  '列注释与表注释说明字段含义，表结构本身即可作为文档；键与约束集中写在建表语句内，便于一次性核对完整性设计。')
code(cut('CREATE DATABASE IF NOT EXISTS ctf', '-- 视图 1'))

page('五  视图功能与实现代码')
h('5.1  公共题库视图 v_challenge_public', 2)
p('公共题库只输出 Status 为 online 的题目，并按外键连接分类表给出方向名称。视图中不包含 FlagHash 与 FlagSalt 两列，'
  '应用即使直接查询视图也无法拿到与 flag 比对相关的任何字段。实测输出了 13 道已上架题目，列名如下表所示。')
table(['视图输出列'], [[c] for c in v['public_view_columns']], [6], center_cols=[])
table(['分类', '题名', '难度', '分值'], v['public_challenges'], [2.6, 8.4, 2, 2], center_cols=[0, 2, 3])

h('5.2  答题记录与得分明细视图', 2)
p('v_submission_record 逐笔列出提交记录：题目分值、是否答对、本次得分与提交时间；是否得分以 Solves 表是否引用该提交为准，'
  '因此重复提交同一道正确 flag 时，记录会显示 0 分，排名数据不会被重复提交影响。'
  'v_score_detail 面向个人得分明细，逐题给出分类、难度、得分与解出时间。')
code(cut('CREATE OR REPLACE VIEW v_submission_record', 'CREATE OR REPLACE VIEW v_total_rank'))
p('以下为错误提交在答题记录中的实际形态，错误提交保留记录但不计分：')
table(['用户名', '分类', '题名', '是否答对', '本次得分'], v['wrong_submission'], [2.4, 2.2, 6.4, 2.8, 3.2])

h('5.3  排行视图 v_total_rank 与 v_category_rank', 2)
p('两个排行视图都用窗口函数 RANK() 计算名次：总分榜按总分降序，同分时先解出者名次靠前；'
  '分类榜以分类分区，分别给出各训练方向的排名。分值来自 Solves 表的计分记录，因此排行与得分明细始终同源。')
code(cut('CREATE OR REPLACE VIEW v_total_rank', '-- ============================================================\n-- 存储过程'))
p('实际数据下的总分榜与分类榜（分类榜列出全部 20 行）：')
table(['名次', '用户名', '总分', '解题数', '最后解题时间'], v['final_total_rank'], [1.8, 3.4, 2.6, 2.6, 6.6])
table(['分类', '名次', '用户名', '分类得分'], v['final_category_rank'], [3.5, 2, 5, 3.5])

page('六  存储过程功能与实现代码')
p('五个存储过程分别承担注册、录题、上架、flag 判定与个人记录查询。判定与计分集中在 sp_submit_flag 内，'
  '应用层只传入参数并读取返回码，业务规则不会散落到多个页面。')

h('6.1  注册过程 sp_register_user', 2)
p('过程内完成用户名格式、口令长度与邮箱格式校验，用 UUID 生成随机盐，并以 SHA2(口令+盐,256) 落库。'
  '用户名唯一约束冲突被捕获为 duplicate 返回码，调用方无需解析数据库错误。')
code(cut('DROP PROCEDURE IF EXISTS sp_register_user', 'DROP PROCEDURE IF EXISTS sp_add_challenge'))

h('6.2  录题过程 sp_add_challenge', 2)
p('过程先校验调用者角色为 admin，再校验难度、分值与 flag 长度；flag 以随机盐散列后入库，题目以草稿状态录入，'
  '同时写入一条操作日志。学生账号调用会得到 denied 返回码。')
code(cut('DROP PROCEDURE IF EXISTS sp_add_challenge', 'DROP PROCEDURE IF EXISTS sp_publish_challenge'))

h('6.3  上架过程 sp_publish_challenge', 2)
p('题目上架后进入公共题库。过程在事务内设置 @operator_uid 并更新状态与上架时间，'
  '状态变更由触发器读取该会话变量，把操作人与新旧状态写入操作日志。')
code(cut('DROP PROCEDURE IF EXISTS sp_publish_challenge', 'DROP PROCEDURE IF EXISTS sp_submit_flag'))

h('6.4  判定过程 sp_submit_flag', 2)
p('这是平台的核心过程：先校验账号状态与题目上架状态，再在事务内按“查重—比对—计分”顺序完成判定。'
  '查重查询 Solves 表，已解出时记录本次提交并返回 duplicate；比对使用 SHA2(提交内容+题目盐,256) 与库中散列比较；'
  '判定正确时写入 Submissions 与 Solves，计分日志由触发器补全。'
  'Solves 的联合主键同时承担并发保护：同一用户对同一题目的并发判分只有一笔能写入成功，另一笔按 duplicate 返回，'
  '因此重复提交无法刷分。过程通过 OUT 参数返回结果码、本次得分与提示文本。')
code(cut('DROP PROCEDURE IF EXISTS sp_submit_flag', 'DROP PROCEDURE IF EXISTS sp_user_records'))
p('实测中的六种返回情形如下：')
table(['提交场景', '返回结果码', '本次得分', '提示信息'], [
    ['首次提交正确 flag', 'correct', '200', '判定正确，本次得分 200 分'],
    ['再次提交同一正确 flag', 'duplicate', '0', '该题已解出，本次提交不重复计分'],
    ['提交错误 flag', 'wrong', '0', 'flag 不正确，可继续尝试'],
    ['向草稿状态题目提交', 'error', '0', '题目未上架，暂不可提交'],
    ['账号不存在时提交', 'error', '0', '用户不存在'],
    ['账号被停用时提交', 'error', '0', '账号已停用，无法提交'],
], [4.6, 2.6, 2.2, 7.6])

h('6.5  个人记录过程 sp_user_records', 2)
p('按用户编号返回逐笔答题记录，包含提交编号、分类、题名、题目分值、是否答对、本次得分与提交时间；'
  '用户不存在时返回一行提示，调用方总能拿到结果集。')
code(cut('DROP PROCEDURE IF EXISTS sp_user_records', '-- ============================================================\n-- 触发器'))
p('实际调用 sp_user_records(2) 返回的记录：')
table(['提交编号', '分类', '题名', '题目分值', '是否答对', '本次得分', '提交时间'],
      [[r[0], r[1], r[2], r[3], r[4], r[5], r[6][:16]] for r in v['sp_user_records']],
      [1.8, 1.8, 4.2, 1.8, 1.8, 1.8, 3.8])

page('七  触发器与自动留痕')
p('三个触发器把留痕动作绑定到数据写入本身：账号注册后自动记录、题目状态变更后自动记录、每次计分后自动记录积分变动。'
  '应用不必在每个页面重复写日志代码，关键操作的记录与业务数据在同一事务内落库。')
code(cut('DROP TRIGGER IF EXISTS trg_users_after_insert', '-- ============================================================\n-- 演示数据'))
p('积分日志在计分时自动生成，TotalAfter 给出变动后的累计总分，使排名变化可以逐笔核对。'
  '以下为初始数据下 zhangsan 与 lisi 的实际日志：')
table(['用户名', '题目编号', '本次得分', '变动后总分', '发生时间'],
      [[r[0], r[1], r[2], r[3], r[4]] for r in v['scorelog_sample']], [3, 2.6, 2.6, 3, 5.8])
p('注册与上架同样自动留痕，以下为操作日志的实际内容：')
table(['操作类型', '操作对象', '操作说明'], v['operation_sample'], [3.2, 3.4, 10.4], center_cols=[0])

page('八  初始数据代码与说明')
p('演示数据按分类、用户、题目、提交、计分的顺序写入，保证外键引用的父记录先于引用存在。'
  '口令与 flag 以加盐散列入库，库中保存的是散列值，登录校验与 flag 比对都在数据库内完成；'
  '解题计分由正确提交派生，分值统一取自题目表，两处数据不会各自维护。')
code(cut('INSERT INTO Categories', '-- 错误提交'))
p('初始数据包含 1 个管理员账号与 10 个学生账号、16 道覆盖五个方向的题目（13 道上架、2 道草稿、1 道下线），'
  '以及 28 次提交与 22 条解题计分，用于演示检索、提交判定、个人记录与两个排行榜的完整效果。'
  '演示账号为 admin（管理员）与 zhangsan 至 xuer（学生），口令见 9.1 节；演示 flag 见 9.4 节。')

page('九  执行方法与验证结果')
h('9.1  初始化与连接', 2)
p('在全新的 MySQL 实例上导入脚本即可得到完整的表、视图、存储过程、触发器与演示数据。'
  '数据库地址、端口、账户与口令按本机实际配置填写。')
code('mysql -h 127.0.0.1 -P 3306 -u root -p < ctf_init.sql\n'
     'mysql -h 127.0.0.1 -P 3306 -u root -p -e "USE ctf; SELECT * FROM v_total_rank;"')
p('应用连接参数为：数据库 ctf，字符集 utf8mb4，事务提交关闭自动提交（autocommit=False），'
  '所有 SQL 使用参数化占位符传入。演示账号 admin / Admin@123，学生账号 zhangsan 等 / Pass@123。')
p('脚本面向全新环境的一次性初始化。已有数据的库需要更新时，重新执行第四节至第七节对应的建表、视图、'
  '存储过程与触发器定义即可完成升级，表内数据不受影响。')

h('9.2  验证查询示例', 2)
code('USE ctf;\n'
     'SELECT * FROM v_challenge_public ORDER BY 题目编号;   -- 公共题库，不含 flag 字段\n'
     'SELECT * FROM v_total_rank;                            -- 总分榜\n'
     'SELECT * FROM v_category_rank WHERE 分类 = \'Web\';      -- 分类榜\n'
     'CALL sp_user_records(2);                               -- 个人答题记录\n'
     'CALL sp_submit_flag(2, 2, \'flag{r3t2l1bc_b4s1c}\', @r, @s, @m);\n'
     'SELECT @r AS 结果码, @s AS 本次得分, @m AS 提示信息;')

h('9.3  实际执行验证', 2)
p('配套脚本已在独立的 MySQL ' + v['mysql_version'] + ' 实例上完整执行一遍，覆盖建库建表、视图、存储过程、触发器与初始数据，'
  '并按正常路径与异常路径逐项验证。验证过程中的写入与删除检查均通过事务回滚恢复，'
  '脚本 work/verify_db.py 可重复运行并输出 work/db_verification.json。' + str(len(v['checks'])) + ' 项检查全部通过：')
table(['#', '验证项与实际结果'], [[i, c] for i, c in enumerate(v['checks'], 1)], [1.2, 15.8], center_cols=[0])

h('9.4  演示 flag 清单', 2)
p('下表列出部分演示题目对应的 flag，用于在本地实例上体验提交、查重与计分流程；'
  '真实录入由 sp_add_challenge 生成随机盐，flag 明文不进入数据库。')
table(['分类', '题名', '演示 flag', '分值'], [
    ['Pwn', 'Welcome Pwn', 'flag{w3lc0me_pwn}', 100],
    ['Pwn', 'ret2libc 基础', 'flag{r3t2l1bc_b4s1c}', 300],
    ['Web', 'SQL 注入初探', 'flag{sql_1nj3ct10n}', 200],
    ['Reverse', '简单异或', 'flag{x0r_1s_34sy}', 150],
    ['Crypto', '凯撒密码', 'flag{c4es4r_c1ph3r}', 100],
    ['Misc', '隐写入门', 'flag{st3g0_1ntr0}', 150],
], [2, 3.6, 8.4, 2], center_cols=[0, 3])

doc.core_properties.title = 'CTF训练竞赛平台数据库设计与实现'
doc.core_properties.subject = '数据库实践 表结构 视图 存储过程 触发器及代码说明'
doc.core_properties.author = ''
doc.core_properties.keywords = 'MySQL,CTF,训练平台,表结构,视图,存储过程,触发器'
path = OUT / 'CTF训练竞赛平台数据库实现说明.docx'
doc.save(path)
print(path.resolve())
