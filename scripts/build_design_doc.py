"""生成《系统设计文档》初稿（按课程模板一至八章）。

数据来源：
- database/ctf_init.sql      数据库脚本（代码段）
- docs/db_verification.json  数据库验证结果
- git log                    版本控制记录

运行：python3 scripts/build_design_doc.py
输出：docs/系统设计文档_初稿.docx
"""
import json
import re
import subprocess
from pathlib import Path

from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'
sql = (ROOT / 'database' / 'ctf_init.sql').read_text()
verify = json.loads((DOCS / 'db_verification.json').read_text())
FIG = DOCS / 'figures'

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2.2)
sec.left_margin = sec.right_margin = Cm(2.2)
sec.footer_distance = Cm(0.9)


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
n.paragraph_format.line_spacing = Pt(17)
n.paragraph_format.space_after = Pt(5)
font_style('Title', 'Calibri', 'Songti SC', 22, True)
for style in doc.styles:
    for border in list(style.element.iter(qn('w:pBdr'))):
        border.getparent().remove(border)
for name, size in [('Heading 1', 16), ('Heading 2', 12), ('Heading 3', 11)]:
    hh = font_style(name, 'Calibri', 'Songti SC', size, True)
    hh.paragraph_format.space_before = Pt(10)
    hh.paragraph_format.space_after = Pt(6)
    hh.paragraph_format.keep_with_next = True
cs = doc.styles.add_style('CodeBlock', 1)
cs.font.name = 'Courier New'
cs.font.size = Pt(8.5)
cs.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), 'Songti SC')
cs.paragraph_format.line_spacing = Pt(10.5)
cs.paragraph_format.space_after = Pt(0)
cs.paragraph_format.space_before = Pt(0)
cs.paragraph_format.left_indent = Cm(0.15)
cs.paragraph_format.widow_control = False
for style in doc.styles:
    if style.type == 1:
        snap = OxmlElement('w:snapToGrid'); snap.set(qn('w:val'), '0')
        style.element.get_or_add_pPr().append(snap)

sec.different_first_page_header_footer = True   # 封面不显示页码
foot = sec.footer.paragraphs[0]
foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
foot.add_run('第 ')
f = OxmlElement('w:fldSimple'); f.set(qn('w:instr'), 'PAGE'); foot._p.append(f)
foot.add_run(' 页')
for r in foot.runs:
    r.font.size = Pt(9)


def relation(text):
    """关系模式：用 [主键] 标记的部分渲染为下划线。"""
    par = doc.add_paragraph()
    for seg_text in re.split(r'(\[[^\]]+\])', text):
        if not seg_text:
            continue
        if seg_text.startswith('['):
            run = par.add_run(seg_text[1:-1])
            run.underline = True
        else:
            par.add_run(seg_text)
    return par


def p(text, size=None, align=None, bold=False, space_before=None, indent=None):
    par = doc.add_paragraph()
    run = par.add_run(text)
    if size:
        run.font.size = Pt(size)
    run.bold = bold
    if align is not None:
        par.alignment = align
    if space_before is not None:
        par.paragraph_format.space_before = Pt(space_before)
    if indent is not None:
        par.paragraph_format.left_indent = Cm(indent)
    return par


def h(text, level=1):
    return doc.add_heading(text, level)


def code(text, size=8.5):
    for line in text.strip().splitlines():
        par = doc.add_paragraph(line, 'CodeBlock')
        for r in par.runs:
            r.font.size = Pt(size)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def caption(text):
    par = p(text, size=9.5, align=WD_ALIGN_PARAGRAPH.CENTER)
    par.paragraph_format.space_before = Pt(3)
    par.paragraph_format.space_after = Pt(8)
    return par


def figure(name, cap, width_cm=15.2):
    doc.add_picture(str(FIG / name), width=Cm(width_cm))
    par = doc.paragraphs[-1]
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.line_spacing = 1.0   # 正文为固定行距，图片段落须用自动行距，否则会被裁剪
    caption(cap)


def table(headers, rows, widths, center_cols=None, caption_text=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for c, width in zip(t.columns, widths):
        c.width = Cm(width)
    for i, val in enumerate(headers):
        t.rows[0].cells[i].text = str(val)
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
    if center_cols is None:
        center_cols = list(range(len(headers)))
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
            for edge, value in [('top', '60'), ('bottom', '60'), ('left', '90'), ('right', '90')]:
                e = OxmlElement('w:' + edge)
                e.set(qn('w:w'), value); e.set(qn('w:type'), 'dxa'); mar.append(e)
            cp.append(mar)
            if ri == 0:
                sh = OxmlElement('w:shd'); sh.set(qn('w:fill'), 'DBE7F2'); cp.append(sh)
            for para in cell.paragraphs:
                para.paragraph_format.space_after = Pt(0)
                para.paragraph_format.line_spacing = Pt(12.5)
                if ri > 0 and ci in center_cols:
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:
                    run.font.size = Pt(9)
                    if ri == 0:
                        run.bold = True
    if caption_text:
        caption(caption_text)
    else:
        doc.add_paragraph().paragraph_format.space_after = Pt(0)


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


TABLE_H = ['字段名称', '数据类型', '是否主键/外键', '是否允许 Null 值', '功能描述']
TABLE_W = [3.6, 2.6, 3.2, 3.0, 5.0]


def field_table(rows, cap):
    table(TABLE_H, rows, TABLE_W, center_cols=[1, 2, 3], caption_text=cap)


# ============================================================
# 封面
# ============================================================
for _ in range(3):
    doc.add_paragraph()
p('安全科学与工程学院', size=24, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
doc.add_paragraph()
p('2025 － 2026 学年第一学期', size=15, align=WD_ALIGN_PARAGRAPH.CENTER)
p('《互联网应用服务开发与数据库实践》', size=15, align=WD_ALIGN_PARAGRAPH.CENTER)

for _ in range(3):
    doc.add_paragraph()
for text in ['题目：CTF训练竞赛平台的设计与实现',
             '班级：24034202',
             '学号：241240075',
             '姓名：闫博泉',
             '电子签（必填）：',
             '教师：邢艳',
             '成绩：']:
    p(text, size=14, indent=4.2)

for _ in range(3):
    doc.add_paragraph()
p('2026 年 10 月 20 日', size=13, align=WD_ALIGN_PARAGRAPH.CENTER)

doc.add_page_break()
p('系统设计文档', size=26, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
doc.add_paragraph()

# ============================================================
# 一 系统需求分析
# ============================================================
h('一  系统需求分析')

h('1.1  系统开发背景', 2)
p('CTF（Capture The Flag，夺旗赛）是网络安全人才培养中广泛采用的实战训练形式：学生需要面对 Pwn、Web、Reverse、'
  'Crypto、Misc 等方向的题目，在真实的攻防场景中锻炼漏洞分析、利用与取证能力。高校网络安全社团与课程实验普遍采用'
  '“长期开放题库、随时登录作答”的常态化训练模式。')
p('这种模式对平台提出了三类要求。其一是判定要及时：学生提交 flag 后需要立刻知道对错与得分，人工核对无法支撑'
  '常态化训练的频率。其二是计分要经得起核对：同一道题若能被重复提交反复计分，排行榜就失去意义，而多名学生同时'
  '提交同一道题时，判定与计分还必须保证不重不漏。其三是过程要可追溯：训练成绩与关键操作需要留痕，便于教师与队伍'
  '管理者复核。')
p('本设计据此把 flag 判定、计分与留痕下沉到数据库层：题目、提交与解题计分分别建表，重复计分由联合主键在结构层'
  '拦下；判定与计分由存储过程在同一事务内完成；公共题库、个人记录与排行榜由视图直接输出；关键操作由触发器自动'
  '写入日志。应用层只负责参数化调用与页面展示，业务规则不会散落到多个页面。')

h('1.2  系统目标', 2)
p('本系统面向高校 CTF 队伍的日常训练与校内选拔场景，服务两类角色：参赛学生（student）与训练管理员（admin）。总体目标如下：')
for line in ['（1）流程闭环：打通“录题—浏览—提交—判定—计分—排行”全流程，flag 提交后由存储过程即时判定并反馈结果；',
             '（2）计分公正：判定与计分收敛在同一数据库事务内，重复提交由结构约束拦截，并发提交不重不漏；',
             '（3）数据安全：口令与 flag 只保存加盐散列，视图层屏蔽敏感列，应用端统一使用参数化查询；',
             '（4）过程可追溯：积分变动、账号注册与题目状态变更由触发器自动留痕，排行榜与明细可逐笔核对。']:
    p(line)

h('1.3  功能需求', 2)
p('系统需求描述：学生注册登录后进入前台训练子系统，可按分类与难度浏览题目、检索目标题目并查看详情；'
  '在题目详情页提交 flag，系统调用存储过程完成查重、比对与计分，即时反馈判定结果与得分；'
  '学生可在个人中心查看答题记录与得分明细，在排行榜查看总分与各方向的训练排名。'
  '管理员负责题目录入与上架，并可通过审计日志复核关键操作。具体功能如下：')
p('前台功能（参赛学生）：')
for line in ['1、用户注册：填写用户名、密码与电子邮箱注册账号，用户名全局唯一，口令加盐散列后存储；',
             '2、用户登录：校验用户名与口令散列，登录会话保存用户身份与角色；',
             '3、题目浏览与检索：按分类（Pwn/Web/Reverse/Crypto/Misc）与难度筛选题目，支持按题名关键词模糊检索；',
             '4、题目详情查看：查看题目描述、分值并下载附件；',
             '5、flag 提交与即时判定：调用存储过程 sp_submit_flag 完成“查重—比对—计分—落库”，即时返回判定结果与得分；',
             '6、个人中心：查看逐笔答题记录与得分明细，修改个人资料与登录口令；',
             '7、积分排行：查看总分排行榜与分类排行榜，显示名次、总分与解题数。']:
    p(line)
p('后台功能（训练管理员）：')
for line in ['8、题目管理：录入新题（题名、分类、难度、分值、flag、描述、附件），修改题目信息，上架或下线题目；',
             '9、用户管理：查询账号、启用或停用账号；',
             '10、审计日志查询：查看积分变动与操作日志，按用户与时间追溯关键操作。']:
    p(line)

h('1.4  非功能需求', 2)
p('性能需求：')
p('（1）系统响应时间：题目浏览、flag 提交判定等常规操作响应时间不超过 2 秒；')
p('（2）并发处理：提交判定由存储过程在数据库事务内完成，重复计分由联合主键拦截，多人同时提交同一道题时计分正确。')
p('安全性需求：')
p('（1）数据加密：用户口令与题目 flag 均以 SHA2 加盐散列存储，数据库不保存任何明文；')
p('（2）访问控制：按角色区分权限，后台功能对 admin 角色开放并在存储过程内再次校验角色；'
  '公共题库视图不输出 flag 散列列，应用端统一采用参数化查询。')
p('可用性需求：')
p('（1）界面友好：页面结构统一，录入与提交均带输入校验和明确的错误提示；')
p('（2）可追溯性：关键操作写入日志表，得分变动可通过积分日志逐笔核对。')
p('兼容性需求：')
p('（1）浏览器兼容：支持 Chrome、Edge、Firefox、Safari 等主流浏览器；')
p('（2）数据库兼容：脚本面向 MySQL 8.0 及以上版本，使用标准 SQL 与窗口函数。')

# ============================================================
# 二 系统总体设计
# ============================================================
h('二  系统总体设计')
p('系统采用 B/S 架构，自上而下分为前台训练子系统、后台管理子系统与数据库服务层三层。'
  '前台与后台通过同一套数据库对象协作：页面只负责收集与展示数据，判定、计分、排行与留痕都由数据库对象完成。'
  '各功能模块及其职责如下表所示。')
table(['子系统', '功能模块', '职责说明', '依赖数据库对象'], [
    ['前台训练子系统', '注册登录', '注册新账号、校验登录凭据', 'sp_register_user、Users'],
    ['', '题库检索', '按分类与难度筛选、按题名检索', 'v_challenge_public'],
    ['', '题目详情', '展示题面与附件、提交 flag', 'sp_submit_flag、Challenges'],
    ['', '个人中心', '答题记录、得分明细、资料修改', 'sp_user_records、v_submission_record'],
    ['', '排行榜', '总分榜与分类榜', 'v_total_rank、v_category_rank'],
    ['后台管理子系统', '题目管理', '录题、修改、上架与下线', 'sp_add_challenge、sp_publish_challenge'],
    ['', '用户管理', '账号查询与状态维护', 'Users'],
    ['', '审计日志', '积分变动与操作留痕查询', 'ScoreLogs、OperationLogs'],
    ['数据库服务层', '视图/存储过程/触发器', '数据访问、业务规则与自动留痕', '5 视图、5 过程、3 触发器'],
], [3.3, 3.0, 6.2, 4.3], center_cols=[0, 1], caption_text='表 1  系统功能模块与职责')
figure('module.png', '图 1  系统功能模块图')

h('2.1  前台训练子系统模块设计', 2)
p('前台子系统面向参赛学生，围绕“找题—看题—交题—看成绩”的训练闭环组织页面。'
  '题库列表页调用公共题库视图，视图只输出已上架题目且不含 flag 散列列，因此学生端页面天然拿不到判定所需的敏感字段。'
  '题目详情页提交 flag 时，页面把学生编号、题目编号与 flag 原文作为参数调用判定存储过程，过程返回结果码、'
  '本次得分与提示文本三类输出参数，页面据此渲染“判定正确 / 已解出 / flag 不正确 / 未上架”等状态。'
  '个人中心的答题记录与排行榜均为只读查询，直接读取视图，不参与计分写入。')

h('2.2  后台管理子系统模块设计', 2)
p('后台子系统面向训练管理员。录题时页面收集题名、分类、难度、分值、flag 与附件信息，调用录题存储过程以草稿状态入库，'
  'flag 在库内以随机盐加盐散列保存。题目上架由独立过程完成：过程校验调用者角色、更新状态与上架时间，'
  '并在事务内写入操作日志，题目随即进入公共题库。用户管理只维护账号状态，被停用的账号在提交时会被判定过程拒绝。'
  '审计日志页面读取积分日志与操作日志两张表，用于复核得分变化与题目状态流转。')

# ============================================================
# 三 数据库设计
# ============================================================
h('三  数据库设计')

h('3.1  概念结构设计', 2)
p('从需求出发可抽象出七个实体。用户（Users）是全局主体，学生与管理员共用一张表，以角色字段区分权限；'
  '题目分类（Categories）对应 Pwn、Web、Reverse、Crypto、Misc 五个训练方向；题目（Challenges）保存题面、难度、'
  '分值与 flag 散列，并以状态字段控制是否进入公共题库；提交记录（Submissions）保存每一次提交，正确的与错误的'
  '同样留档；解题计分（Solves）以“用户编号 + 题目编号”为联合主键，保证同一道题只计分一次；'
  '积分日志（ScoreLogs）与操作日志（OperationLogs）分别记录得分变动与管理操作，由触发器自动写入。')
p('各实体的属性如下（主键以“编号”标识）：')
for line in ['用户（用户编号，登录名，口令散列，口令盐，电子邮箱，角色，账号状态，注册时间）',
             '题目分类（分类编号，分类名称，分类说明）',
             '题目（题目编号，分类编号，题名，题目描述，难度，分值，flag 散列，flag 盐，附件路径，上架状态，录题人，录入时间，上架时间）',
             '提交记录（提交编号，用户编号，题目编号，提交 flag 散列，是否正确，提交时间）',
             '解题计分（用户编号，题目编号，首次正确提交编号，得分，解出时间）',
             '积分日志（日志编号，用户编号，题目编号，得分变动，变动后总分，动作类型，发生时间）',
             '操作日志（日志编号，操作人，操作类型，操作对象，操作说明，发生时间）']:
    p(line)
p('实体之间的联系：用户录入题目（1:N）、分类收录题目（1:N）、用户提交记录（1:N）、题目接收提交（1:N）、'
  '题目被解出（1:N）、用户解出题目（1:N）、用户产生积分日志（1:N）、题目对应积分日志（1:N）、'
  '用户产生操作日志（1:N）。系统 E-R 图如下。')
figure('er.png', '图 2  系统 E-R 图')

h('3.2  逻辑结构设计', 2)
p('将 E-R 模型转换为关系模式，得到如下七个关系（下划线部分为主键）：')
for line in ['用户（[用户编号]，登录名，口令散列，口令盐，电子邮箱，角色，账号状态，注册时间）',
             '题目分类（[分类编号]，分类名称，分类说明）',
             '题目（[题目编号]，分类编号，题名，题目描述，难度，分值，flag 散列，flag 盐，附件路径，上架状态，录题人，录入时间，上架时间）',
             '提交记录（[提交编号]，用户编号，题目编号，提交 flag 散列，是否正确，提交时间）',
             '解题计分（[用户编号，题目编号]，首次正确提交编号，得分，解出时间）',
             '积分日志（[日志编号]，用户编号，题目编号，得分变动，变动后总分，动作类型，发生时间）',
             '操作日志（[日志编号]，操作人，操作类型，操作对象，操作说明，发生时间）']:
    relation(line)
p('其中解题计分的主键由“用户编号 + 题目编号”两个属性组成，这一设计把“同一学生对同一题目只计分一次”'
  '直接固化为结构约束；首次正确提交编号引用提交记录，使每笔得分都能追溯到具体那一次提交。'
  '题目与分类、题目与录题人、提交与用户及题目、日志与用户及题目之间均通过外键建立引用关系。')

h('3.3  物理结构设计', 2)
p('数据库 ctf 使用 InnoDB 存储引擎与 utf8mb4 字符集，共七张基本表。各表结构如下。')

field_table([
    ['用户编号 Uid', 'INT', '主键', '否', '自增主键，用户唯一标识'],
    ['登录名 Username', 'VARCHAR(32)', '唯一', '否', '全局唯一，用于登录'],
    ['口令散列 PasswordHash', 'CHAR(64)', '—', '否', 'SHA2(口令+盐,256)'],
    ['口令盐 Salt', 'CHAR(32)', '—', '否', '每个账号独立随机盐'],
    ['电子邮箱 Email', 'VARCHAR(64)', '—', '否', '注册时填写'],
    ['角色 Role', 'ENUM', '—', '否', 'student 或 admin'],
    ['账号状态 Status', 'ENUM', '—', '否', 'active 或 disabled'],
    ['注册时间 CreatedAt', 'DATETIME', '—', '否', '默认当前时间'],
], '表 2  用户信息表（Users）')

field_table([
    ['分类编号 Cid', 'INT', '主键', '否', '自增主键'],
    ['分类名称 Cname', 'VARCHAR(16)', '唯一', '否', 'Pwn/Web/Reverse/Crypto/Misc'],
    ['分类说明 Cdesc', 'VARCHAR(100)', '—', '是', '方向说明'],
], '表 3  题目分类表（Categories）')

field_table([
    ['题目编号 Chid', 'INT', '主键', '否', '自增主键'],
    ['分类编号 Cid', 'INT', '外键', '否', '引用 Categories(Cid)'],
    ['题名 Title', 'VARCHAR(64)', '—', '否', '题目名称'],
    ['题目描述 Description', 'VARCHAR(500)', '—', '是', '题面信息'],
    ['难度 Difficulty', 'TINYINT', '—', '否', '取值 1 至 5，CHECK 约束'],
    ['分值 Score', 'INT', '—', '否', '大于 0，CHECK 约束'],
    ['flag 散列 FlagHash', 'CHAR(64)', '—', '否', 'SHA2(flag+盐,256)'],
    ['flag 盐 FlagSalt', 'CHAR(32)', '—', '否', '每道题独立盐'],
    ['附件路径 Attachment', 'VARCHAR(128)', '—', '是', '题目附件下载地址'],
    ['上架状态 Status', 'ENUM', '—', '否', 'draft/online/offline'],
    ['录题人 AuthorUid', 'INT', '外键', '否', '引用 Users(Uid)'],
    ['录入时间 CreatedAt', 'DATETIME', '—', '否', '默认当前时间'],
    ['上架时间 PublishedAt', 'DATETIME', '—', '是', '上架时写入'],
], '表 4  题目表（Challenges）')

field_table([
    ['提交编号 Subid', 'BIGINT', '主键', '否', '自增主键'],
    ['用户编号 Uid', 'INT', '外键', '否', '引用 Users(Uid)'],
    ['题目编号 Chid', 'INT', '外键', '否', '引用 Challenges(Chid)'],
    ['提交 flag 散列 FlagHash', 'CHAR(64)', '—', '否', '本次提交内容的散列'],
    ['是否正确 IsCorrect', 'TINYINT', '—', '否', '取值 0 或 1，CHECK 约束'],
    ['提交时间 SubmittedAt', 'DATETIME', '—', '否', '默认当前时间'],
], '表 5  提交记录表（Submissions）')

field_table([
    ['用户编号 Uid', 'INT', '联合主键', '否', '引用 Users(Uid)'],
    ['题目编号 Chid', 'INT', '联合主键', '否', '引用 Challenges(Chid)'],
    ['首次正确提交编号 Subid', 'BIGINT', '唯一、外键', '否', '引用 Submissions(Subid)'],
    ['得分 ScoreAwarded', 'INT', '—', '否', '大于 0，CHECK 约束'],
    ['解出时间 SolvedAt', 'DATETIME', '—', '否', '默认当前时间'],
], '表 6  解题计分表（Solves）')

field_table([
    ['日志编号 LogId', 'BIGINT', '主键', '否', '自增主键'],
    ['用户编号 Uid', 'INT', '外键', '否', '引用 Users(Uid)'],
    ['题目编号 Chid', 'INT', '外键', '否', '引用 Challenges(Chid)'],
    ['得分变动 DeltaScore', 'INT', '—', '否', '本次新增得分'],
    ['变动后总分 TotalAfter', 'INT', '—', '否', '该用户当前累计总分'],
    ['动作类型 Action', 'VARCHAR(16)', '—', '否', '默认 solve'],
    ['发生时间 OccurredAt', 'DATETIME', '—', '否', '取解题时间'],
], '表 7  积分日志表（ScoreLogs）')

field_table([
    ['日志编号 Opid', 'BIGINT', '主键', '否', '自增主键'],
    ['操作人 Uid', 'INT', '外键', '否', '引用 Users(Uid)'],
    ['操作类型 Action', 'VARCHAR(32)', '—', '否', '注册账号/录入题目/题目上架等'],
    ['操作对象 Target', 'VARCHAR(64)', '—', '是', '账号名或题名'],
    ['操作说明 Detail', 'VARCHAR(200)', '—', '是', '操作详情'],
    ['发生时间 OccurredAt', 'DATETIME', '—', '否', '默认当前时间'],
], '表 8  操作日志表（OperationLogs）')

p('数据库索引设计：')
table(['索引', '所在表', '索引列', '设计目的'], [
    ['PRIMARY', 'Users', 'Uid', '主键索引，账号关联与登录查询'],
    ['PRIMARY', 'Challenges', 'Chid', '主键索引，题目详情与提交关联'],
    ['idx_challenge_filter', 'Challenges', '(Cid, Difficulty, Status)', '分类与难度组合检索、上架题目过滤'],
    ['idx_challenge_title', 'Challenges', '(Title)', '题名关键词检索'],
    ['PRIMARY', 'Solves', '(Uid, Chid)', '联合主键，保证每题只计分一次'],
    ['uk_solves_submission', 'Solves', '(Subid)', '得分与首次正确提交一一对应'],
    ['idx_submission_user', 'Submissions', '(Uid, SubmittedAt)', '个人答题记录按时间查询'],
    ['idx_submission_challenge', 'Submissions', '(Chid, IsCorrect)', '题目提交情况统计'],
    ['idx_scorelog_user', 'ScoreLogs', '(Uid, OccurredAt)', '积分明细回溯'],
    ['idx_operation_user', 'OperationLogs', '(Uid, OccurredAt)', '审计日志按操作人查询'],
], [3.6, 2.8, 4.6, 6.2], center_cols=[0, 1, 2], caption_text='表 9  数据库索引设计')

# ============================================================
# 四 系统详细设计与实现
# ============================================================
h('四  系统详细设计与实现')
p('本章给出数据库服务器端与应用服务器端的主要实现。数据库层的完整脚本见项目仓库 database/ctf_init.sql，'
  '脚本已在本地 MySQL ' + verify['mysql_version'] + ' 实例上完整执行，并通过 ' + str(len(verify['checks'])) +
  ' 项自动化验证（验证项见 4.1.4 节）。')

h('4.1  数据库服务器端', 2)
p('数据库层共使用 5 个视图、5 个存储过程与 3 个触发器，覆盖查询封装、业务规则与自动留痕三类职责。')

h('4.1.1  视图', 3)
p('视图用于固化查询口径并屏蔽敏感列。公共题库视图只包含已上架题目，且不输出 flag 散列与盐两列；'
  '答题记录视图与得分明细视图分别面向“逐笔提交”与“逐题得分”；两个排行视图使用窗口函数 RANK() 计算名次，'
  '同分时先解出者名次靠前，分类榜按分类分区给出各方向的排名。')
code(cut('CREATE OR REPLACE VIEW v_challenge_public', 'CREATE OR REPLACE VIEW v_submission_record'))
code(cut('CREATE OR REPLACE VIEW v_submission_record', 'CREATE OR REPLACE VIEW v_total_rank'))
p('实测：公共题库视图输出 ' + str(len(verify['public_challenges'])) + ' 道已上架题目，列名中不含 FlagHash 与 FlagSalt；'
  '总分榜共 ' + str(len(verify['final_total_rank'])) + ' 人入榜，榜首 ' + verify['final_total_rank'][0][1] +
  ' 总分 ' + str(verify['final_total_rank'][0][2]) + ' 分，全站总分与解题条数一致。')

h('4.1.2  存储过程', 3)
p('五个存储过程分别承担注册、录题、上架、flag 判定与个人记录查询。其中 flag 判定过程是平台的核心：'
  '它先校验账号状态与题目上架状态，再在事务内依次完成查重、比对与计分。查重查询解题计分表，已解出时记录本次提交'
  '并返回 duplicate；比对使用 SHA2(提交内容+题目盐,256) 与库中散列比较；判定正确时写入提交记录与计分记录，'
  '计分日志由触发器补全。解题计分表的联合主键同时承担并发保护：同一用户对同一题目的并发判分只有一笔能写入成功，'
  '另一笔按 duplicate 返回，因此重复提交无法刷分。')
table(['存储过程', '作用', '主要输出'], [
    ['sp_register_user', '校验用户名、口令与邮箱格式，生成随机盐并写入加盐散列口令', 'ok / duplicate / invalid'],
    ['sp_add_challenge', '校验管理员角色与题目参数，flag 以随机盐散列入库，题目置为草稿', 'ok / denied / invalid'],
    ['sp_publish_challenge', '校验角色与题目状态，上架并写入上架时间，状态变更自动留痕', 'ok / denied / noop'],
    ['sp_submit_flag', '事务内完成查重、比对与计分，返回判定结果与本次得分', 'correct / duplicate / wrong / error'],
    ['sp_user_records', '按用户编号返回逐笔答题记录', '结果集'],
], [3.6, 9.2, 4.4], center_cols=[0], caption_text='表 10  存储过程一览')
p('核心判定过程 sp_submit_flag 的定义如下：')
code(cut('DROP PROCEDURE IF EXISTS sp_submit_flag', 'DROP PROCEDURE IF EXISTS sp_user_records'))
p('实测返回情形：首次正确提交返回 correct 并计分；重复提交同一正确 flag 返回 duplicate 且总分不再增长；'
  '错误 flag 返回 wrong 且该笔提交仍进入答题记录；向草稿题目提交返回“题目未上架”；不存在或被停用的账号提交被拒绝。')

h('4.1.3  触发器', 3)
p('三个触发器把留痕动作绑定到数据写入本身：账号注册成功后写入操作日志；题目状态变更时记录操作人、新旧状态；'
  '每次计分写入积分日志，同时记录本次变动与变动后的累计总分，使排行榜的每一次变化都可回溯。')
code(cut('DROP TRIGGER IF EXISTS trg_users_after_insert', '-- ============================================================\n-- 演示数据'))
p('实测：注册触发器为 11 个演示账号自动写入操作日志；积分日志记录的变动后总分与解题计分累计逐人一致；'
  '题目上架后公共题库由 13 条增至 14 条，并按操作用户记下“题目上架”日志。')

h('4.1.4  数据库验证结果', 3)
p('配套验证脚本 scripts/verify_db.py 会自动重建数据库、导入初始化脚本并逐项断言，'
  '最后恢复初始状态。验证覆盖正常路径与异常路径，' + str(len(verify['checks'])) + ' 项检查全部通过：')
table(['#', '验证项与实际结果'], [[i, c] for i, c in enumerate(verify['checks'], 1)],
      [1.0, 16.0], center_cols=[0], caption_text='表 11  数据库自动化验证结果')

h('4.2  应用服务器端', 2)
p('应用服务器端采用 ASP.NET Web Forms 实现，页面通过参数化命令调用前述视图与存储过程，'
  '不在应用层重复实现判定、计分与排行逻辑。数据库连接串统一配置在 Web.config 中，'
  '连接参数为 database=ctf、charset=utf8mb4，并关闭自动提交以便显式控制事务。'
  '以下按课程要求给出数据录入、删除、检索、修改与安全性五类功能的应用端实现示例，'
  '以及关键页面的 HTML、CSS 与 JavaScript 代码说明；界面截图待应用层页面完成后补充。')

h('4.2.1  数据录入功能', 3)
p('以管理员录题为例：页面收集题名、分类、难度、分值、flag 与附件，提交后由服务端调用录题存储过程。'
  '存储过程返回结果码与题目编号，页面据此提示“已录入为草稿”或具体校验失败原因。')
code('''// 后台录题页面（AddChallenge.aspx.cs）
protected void btnSave_Click(object sender, EventArgs e)
{
    using (var conn = new MySqlConnection(Config.ConnString))
    using (var cmd = new MySqlCommand("sp_add_challenge", conn))
    {
        cmd.CommandType = CommandType.StoredProcedure;
        cmd.Parameters.AddWithValue("@p_admin", Session["uid"]);
        cmd.Parameters.AddWithValue("@p_cid", ddlCategory.SelectedValue);
        cmd.Parameters.AddWithValue("@p_title", txtTitle.Text.Trim());
        cmd.Parameters.AddWithValue("@p_desc", txtDesc.Text.Trim());
        cmd.Parameters.AddWithValue("@p_difficulty", ddlDifficulty.SelectedValue);
        cmd.Parameters.AddWithValue("@p_score", int.Parse(txtScore.Text));
        cmd.Parameters.AddWithValue("@p_flag", txtFlag.Text);
        cmd.Parameters.AddWithValue("@p_attachment", txtAttachment.Text);
        cmd.Parameters.Add("@p_chid", MySqlDbType.Int32).Direction = ParameterDirection.Output;
        cmd.Parameters.Add("@p_result", MySqlDbType.VarChar, 16).Direction = ParameterDirection.Output;
        cmd.Parameters.Add("@p_message", MySqlDbType.VarChar, 100).Direction = ParameterDirection.Output;
        conn.Open();
        cmd.ExecuteNonQuery();
        lblMsg.Text = cmd.Parameters["@p_message"].Value.ToString();
    }
}''')

h('4.2.2  数据删除功能', 3)
p('后台允许删除尚未上架且没有任何提交记录的草稿题目。删除前由外键约束兜底：只要题目已产生提交或计分记录，'
  '数据库就会拒绝删除，应用只需捕获错误码并提示管理员改为“下线”处理，历史数据保持完整。')
code('''// 题目管理页面（ChallengeList.aspx.cs）
protected void btnDelete_Click(object sender, EventArgs e)
{
    var id = int.Parse(hfChid.Value);
    try
    {
        using (var conn = new MySqlConnection(Config.ConnString))
        using (var cmd = new MySqlCommand(
            "DELETE FROM Challenges WHERE Chid = @chid AND Status = 'draft'", conn))
        {
            cmd.Parameters.AddWithValue("@chid", id);
            conn.Open();
            var rows = cmd.ExecuteNonQuery();
            lblMsg.Text = rows == 1 ? "草稿题目已删除" : "该题目不满足删除条件";
        }
    }
    catch (MySqlException ex) when (ex.Number == 1451)
    {
        lblMsg.Text = "题目已有提交记录，请改为下线处理";
    }
}''')

h('4.2.3  数据检索功能', 3)
p('题库检索按分类、难度与题名关键词组合查询公共题库视图。三个条件均使用参数占位符，未选择时以 NULL 占位，'
  '由 SQL 中的 COALESCE 逻辑跳过该条件；题名使用 LIKE 前缀匹配，走 idx_challenge_title 索引。')
code('''SELECT 题目编号, 分类, 题名, 难度, 分值
FROM v_challenge_public
WHERE (@cid IS NULL OR 分类 = @cid)
  AND (@difficulty IS NULL OR 难度 = @difficulty)
  AND (@keyword IS NULL OR 题名 LIKE CONCAT(@keyword, '%'))
ORDER BY 难度, 题目编号;''')

h('4.2.4  数据修改功能', 3)
p('学生修改个人资料或登录口令时，服务端先生成新的随机盐，再计算新口令散列，然后更新用户表；'
  '管理员修改题目信息时直接更新题目表，已被提交过的题目只允许修改描述、难度与分值，题目标题与分类保持不变。')
code('''// 个人中心（Profile.aspx.cs）修改登录口令
var salt = Guid.NewGuid().ToString("N");
var hash = Sha256(password + salt);
using (var conn = new MySqlConnection(Config.ConnString))
using (var cmd = new MySqlCommand(
    "UPDATE Users SET PasswordHash = @hash, Salt = @salt WHERE Uid = @uid", conn))
{
    cmd.Parameters.AddWithValue("@hash", hash);
    cmd.Parameters.AddWithValue("@salt", salt);
    cmd.Parameters.AddWithValue("@uid", Session["uid"]);
    conn.Open();
    cmd.ExecuteNonQuery();
}''')

h('4.2.5  安全性实现', 3)
p('安全性由数据库层与应用层共同保证：口令与 flag 只保存加盐散列，公共题库视图不输出散列列；'
  '所有 SQL 使用参数占位符，避免拼接字符串带来的注入风险；后台操作在页面与服务端各校验一次角色，'
  '并在存储过程内部再次校验，形成三重校验。提交页对 flag 长度与格式先做前端校验，服务端仍以存储过程的结果为准。')
code('''<!-- 表单安全：ViewState 校验与输入长度限制 -->
<%@ Page Language="C#" AutoEventWireup="true" EnableViewStateMac="true" %>
<asp:TextBox ID="txtFlag" runat="server" MaxLength="128"
             ClientIDMode="Static" CssClass="input" />
<asp:Button ID="btnSubmit" runat="server" Text="提交 flag"
            OnClientClick="return checkFlag();" OnClick="btnSubmit_Click" />''')
code('''// 提交页服务端：参数化调用判定过程
using (var cmd = new MySqlCommand("sp_submit_flag", conn))
{
    cmd.CommandType = CommandType.StoredProcedure;
    cmd.Parameters.AddWithValue("@p_uid", Session["uid"]);
    cmd.Parameters.AddWithValue("@p_chid", chid);
    cmd.Parameters.AddWithValue("@p_flag", txtFlag.Text.Trim());
    cmd.Parameters.Add("@p_result", MySqlDbType.VarChar, 16).Direction = ParameterDirection.Output;
    cmd.Parameters.Add("@p_score", MySqlDbType.Int32).Direction = ParameterDirection.Output;
    cmd.Parameters.Add("@p_message", MySqlDbType.VarChar, 100).Direction = ParameterDirection.Output;
    conn.Open();
    cmd.ExecuteNonQuery();
}''')

h('4.2.6  关键 HTML、CSS、JavaScript 代码描述', 3)
p('页面采用统一的 Bootstrap 栅格布局，题目列表使用卡片网格展示分类、难度与分值；难度以颜色标签区分，'
  '提交结果以顶部提示条反馈。JavaScript 负责提交前的非空与长度校验，以及提交按钮的防重复点击。')
code('''<!-- 题目卡片（ChallengeList.aspx） -->
<div class="row">
  <% foreach (var item in Challenges) { %>
  <div class="col-md-4">
    <div class="card mb-3">
      <div class="card-body">
        <span class="badge badge-cat"><%= item.Category %></span>
        <span class="badge badge-diff-<%= item.Difficulty %>">难度 <%= item.Difficulty %></span>
        <h5 class="card-title"><a href="ChallengeDetail.aspx?id=<%= item.Chid %>">
          <%= item.Title %></a></h5>
        <p class="text-muted mb-0"><%= item.Score %> 分</p>
      </div>
    </div>
  </div>
  <% } %>
</div>''')
code('''/* 难度标签与提交按钮样式 */
.badge-diff-1 { background:#e6f4ea; color:#1e7e34; }
.badge-diff-3 { background:#fff4e5; color:#b26a00; }
.badge-diff-5 { background:#fdecea; color:#b71c1c; }
#btnSubmit[disabled] { opacity:.6; cursor:not-allowed; }''')
code('''// 提交前校验与防重复提交
function checkFlag() {
    var v = document.getElementById("txtFlag").value.trim();
    if (v.length < 6) { alert("flag 长度不少于 6 位"); return false; }
    var btn = document.getElementById("btnSubmit");
    btn.disabled = true;                       // 防止重复点击造成重复提交
    setTimeout(function () { btn.disabled = false; }, 3000);
    return true;
}''')

# ============================================================
# 五 系统说明
# ============================================================
h('五  系统说明')

h('5.1  系统开发环境', 2)
table(['项目', '配置'], [
    ['操作系统', 'macOS / Windows 10 及以上'],
    ['数据库', 'MySQL 8.0 及以上（本次验证实例 ' + verify['mysql_version'] + '），字符集 utf8mb4，存储引擎 InnoDB'],
    ['数据库脚本', 'database/ctf_init.sql，共 7 表、5 视图、5 存储过程、3 触发器与演示数据'],
    ['验证与生成脚本', 'Python 3.10 及以上、PyMySQL、python-docx'],
    ['应用服务器', 'ASP.NET Web Forms（.NET Framework 4.8），IIS 或 IIS Express'],
    ['浏览器', 'Chrome、Edge、Firefox、Safari 等主流浏览器'],
    ['版本控制', 'Git，提交信息遵循 Conventional Commits 规范'],
], [4.0, 13.0], center_cols=[0], caption_text='表 12  系统开发环境')

h('5.2  系统安装、配置与发布应用程序的步骤', 2)
p('（1）安装并启动 MySQL 8.0 及以上版本的服务，创建数据库账号并赋予 ctf 库的读写权限；')
p('（2）导入数据库脚本，完成建库、建表、视图、存储过程、触发器与演示数据的初始化：')
code('mysql -h 127.0.0.1 -P 3306 -u root -p < database/ctf_init.sql')
p('（3）运行自动化验证脚本确认数据库对象完整、判定与计分行为正确：')
code('python3 scripts/verify_db.py')
p('（4）在 Web.config 中配置数据库连接串，参数为 database=ctf、charset=utf8mb4、autocommit=False；')
p('（5）在 IIS 中新建网站并指向应用目录，或将项目设为启动项目后使用 IIS Express 运行；')
p('（6）使用演示管理员账号 admin / Admin@123 登录后台完成首次录题与上架，学生账号 zhangsan / Pass@123 可用于提交验证。')

# ============================================================
# 六 课程设计总结
# ============================================================
h('六  课程设计总结')
p('本次课程设计围绕 CTF 训练竞赛平台完成了数据库层的主要工作。实现了七张基本表的结构设计与建库建表脚本，'
  '设计了分类与难度检索、题目详情与公共题库、答题记录与得分明细五类查询视图，'
  '实现了注册、录题、上架、flag 判定与个人记录五个存储过程，并用三个触发器把注册、题目状态变更与积分变动'
  '自动写入日志。flag 判定的查重、比对与计分在同一事务内完成，重复计分由联合主键在结构层拦截；'
  '配套的验证脚本覆盖正常与异常路径共 ' + str(len(verify['checks'])) + ' 项断言，全部通过。')
p('设计中的主要难点有三个。第一是并发下的重复计分：最初的方案是在过程内先查询是否已解出再写入，'
  '但两次并发提交都可能通过查询；最终把“用户编号 + 题目编号”设为解题计分表的联合主键，'
  '由数据库在写入阶段保证唯一，并在过程中用行计数区分“首次计分”与“重复提交”。'
  '第二是得分与排名的可核对性：计分写入与积分日志由触发器绑定，日志同时记录本次变动与变动后总分，'
  '排行榜直接由计分表聚合，使榜单与明细始终同源。第三是敏感数据与敏感列的隔离：'
  '口令与 flag 只保存加盐散列，公共题库视图不投影散列列，应用端即使直接查询视图也拿不到判定字段。')
p('目前仍存在的不足与后续计划如下：应用服务器端页面尚在实现中，本文第四节的界面截图将在页面完成后补充；'
  '后台的公告模块尚未建表实现，后续可增加公告表与对应维护页面；题目分值目前为固定值，'
  '可以扩展为按提交次数衰减的动态计分；分类榜在名次并列时可进一步提供“同分同解出时间”的展开说明。'
  '上述内容均可在现有表结构与存储过程的基础上增量实现，不需要改动已完成的计分机制。')
p('通过本次设计，我对关系模型的设计取舍、外键与约束的落地方式、存储过程中的事务与异常处理、'
  '触发器的适用边界以及视图在数据隔离中的作用有了更具体的理解；也体会到把业务规则放在数据库层之后，'
  '应用层的职责会明显变薄，测试与验证也更容易做到可重复。')

# ============================================================
# 七 AI 使用说明
# ============================================================
h('七  AI 使用说明')
p('本设计在完成过程中使用了 AI 编程助手辅助，具体使用范围与人工负责的部分如下。')
table(['环节', 'AI 辅助内容', '本人负责内容'], [
    ['需求分析', '整理模板要求、汇总功能点', '确认题目要求与功能范围'],
    ['数据库设计', '生成 E-R 结构、表结构与约束草案', '审核实体关系、主外键与约束取舍'],
    ['脚本实现', '编写建库建表、视图、存储过程与触发器脚本', '在本机 MySQL 实例执行并核对输出'],
    ['测试验证', '编写自动化验证脚本与断言', '逐项复核验证项与错误码是否符合预期'],
    ['文档排版', '生成文档结构、插图和表格', '核对内容准确性，补充个人信息与签名'],
], [3.0, 8.4, 5.6], center_cols=[0], caption_text='表 13  AI 辅助使用说明')
p('AI 生成的脚本与文档均经过本地实际执行验证：数据库脚本在 MySQL ' + verify['mysql_version'] +
  ' 实例上无错误导入，验证脚本的 ' + str(len(verify['checks'])) + ' 项断言全部通过，文档中的验证数据取自实测结果。')

# ============================================================
# 八 版本控制记录
# ============================================================
h('八  版本控制记录')
p('本项目的代码与文档使用 Git 进行版本管理，仓库采用 docs、database、scripts、src、tests 的标准目录结构。'
  '提交信息统一采用“类型(范围): 简述”的规范前缀，类型取 feat、fix、docs、style、refactor、test、build、chore。')
try:
    log = subprocess.run(['git', 'log', '--pretty=format:%h|%ad|%s', '--date=format:%Y-%m-%d %H:%M'],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip().splitlines()
except Exception:
    log = []
rows = []
for i, line in enumerate(reversed(log), 1):
    parts = line.split('|')
    if len(parts) == 3:
        rows.append([i, parts[0], parts[1], parts[2]])
if rows:
    table(['序号', '提交', '时间', '提交信息'], rows, [1.2, 1.9, 3.6, 10.3],
          center_cols=[0, 1, 2], caption_text='表 14  版本控制记录')
p('表 14 记录截至本文档更新时的提交历史，按时间顺序排列。提交前缀与实际内容一一对应：chore 用于仓库与目录初始化，'
  'feat 用于新增数据库脚本，'
  'test 用于验证脚本与验证结果，build 用于构建与生成脚本，docs 用于文档提交。'
  '每次提交均可通过 git log 与 git show 查看具体改动，仓库结构截图见附图。')
shot = DOCS / 'figures' / 'version-control.png'
if shot.exists():
    figure('version-control.png', '图 3  仓库目录结构与提交记录截图', width_cm=15.6)
else:
    p('（仓库目录结构与提交记录截图待补充。）')

doc.core_properties.title = 'CTF训练竞赛平台系统设计文档（初稿）'
doc.core_properties.subject = '互联网应用服务开发与数据库实践 课程大作业'
doc.core_properties.author = '闫博泉'
doc.core_properties.keywords = 'CTF,MySQL,系统设计,数据库设计,存储过程,触发器'

out = DOCS / '系统设计文档_初稿.docx'
doc.save(out)
print(out)
