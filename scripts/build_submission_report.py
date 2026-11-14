"""按课程模板生成 24 页系统设计报告。先生成 docs/figures/web-*.png。"""
import json
import re
import textwrap
import subprocess
from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT/'docs'; FIG = DOCS/'figures'
old = Document(DOCS/'系统设计文档_初稿.docx')
sql = (ROOT/'database/ctf_init.sql').read_text()
app = (ROOT/'src/web/app.py').read_text()
verify = json.loads((DOCS/'db_verification.json').read_text())
web = json.loads((DOCS/'web_verification.json').read_text())
D = Document(); S = D.sections[0]
S.page_width = Cm(21); S.page_height = Cm(29.7)
S.top_margin = S.bottom_margin = Cm(2.1)
S.left_margin = S.right_margin = Cm(2.2)
S.footer_distance = Cm(.8); S.different_first_page_header_footer = True
for name, size, bold in [('Normal',12,False),('Title',22,True),('Heading 1',16,True),('Heading 2',14,True),('Heading 3',12,True)]:
    st=D.styles[name];st.font.name='Times New Roman';st.font.size=Pt(size);st.font.bold=bold;st.font.color.rgb=RGBColor(0,0,0)
    st.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'宋体')
    st.paragraph_format.line_spacing=1
    st.paragraph_format.space_after=Pt(6)
    st.paragraph_format.space_before=Pt(9 if name.startswith('Heading') else 0)
for st in D.styles:
    for e in list(st.element.iter(qn('w:pBdr'))):e.getparent().remove(e)
code_style=D.styles.add_style('Code',1);code_style.base_style=D.styles['Normal']
code_style.paragraph_format.space_after=Pt(0);code_style.paragraph_format.space_before=Pt(0)
foot=S.footer.paragraphs[0];foot.alignment=WD_ALIGN_PARAGRAPH.CENTER
foot.add_run('第 ');field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');foot._p.append(field);foot.add_run(' 页')

def p(text='',bold=False):
    par=D.add_paragraph();r=par.add_run(text);r.bold=bold;return par

def h(text,level=2):return D.add_heading(text,level)
def page(title):
    D.add_page_break();h(title,1)

def code(text):
    for line in text.strip().splitlines():D.add_paragraph(line,'Code')

def table(headers,rows,widths=None):
    widths=widths or [16.6/len(headers)]*len(headers)
    t=D.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    for i,(c,w) in enumerate(zip(t.columns,widths)):c.width=Cm(w);t.rows[0].cells[i].text=headers[i]
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row):cells[i].text=str(v)
    borders=OxmlElement('w:tblBorders')
    for name in ['top','bottom','left','right','insideH','insideV']:
        e=OxmlElement('w:'+name)
        for k,v in [('val','single'),('sz','4'),('color','D9D9D9')]:e.set(qn('w:'+k),v)
        borders.append(e)
    t._tbl.tblPr.append(borders)
    for ri,row in enumerate(t.rows):
        pr=row._tr.get_or_add_trPr();pr.append(OxmlElement('w:cantSplit'))
        if ri==0:pr.append(OxmlElement('w:tblHeader'))
        for ci,c in enumerate(row.cells):
            c.width=Cm(widths[ci]);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            mar=OxmlElement('w:tcMar')
            for side,val in [('top','65'),('bottom','65'),('left','80'),('right','80')]:
                e=OxmlElement('w:'+side);e.set(qn('w:w'),val);e.set(qn('w:type'),'dxa');mar.append(e)
            c._tc.get_or_add_tcPr().append(mar)
            if ri==0:
                fill=OxmlElement('w:shd');fill.set(qn('w:fill'),'E5EBF2');c._tc.get_or_add_tcPr().append(fill)
            for par in c.paragraphs:
                par.paragraph_format.space_after=Pt(0);par.paragraph_format.space_before=Pt(0);par.paragraph_format.line_spacing=1
                for r in par.runs:r.font.size=Pt(12);r.bold=(ri==0)
    p();return t

def image(name,caption,width=16.4):
    path=FIG/name
    assert path.exists(),path
    par=D.add_paragraph();par.alignment=WD_ALIGN_PARAGRAPH.CENTER
    par.add_run().add_picture(str(path),width=Cm(width))
    par.paragraph_format.keep_with_next=True
    cap=p(caption);cap.alignment=WD_ALIGN_PARAGRAPH.CENTER


def cut(start,end,source=app):
    return source[source.index(start):source.index(end,source.index(start))].strip()

def codeshot(name,start,end):
    raw=cut(start,end)
    indent=len(start)-len(start.lstrip())
    original=textwrap.dedent(' '*indent+raw).splitlines()
    f=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',22)
    probe=ImageDraw.Draw(Image.new('RGB',(1,1)))
    lines=[]
    for line in original:
        rest=line
        while probe.textlength(rest,font=f)>1150:
            n=1
            while n<len(rest) and probe.textlength(rest[:n+1],font=f)<=1150:n+=1
            split=rest.rfind(' ',0,n)
            if split>n//2:n=split
            lines.append(rest[:n]);rest='    '+rest[n:].lstrip()
        lines.append(rest)
    canvas=Image.new('RGB',(1200,len(lines)*32+34),'#f7f9fc');dr=ImageDraw.Draw(canvas)
    for i,line in enumerate(lines):dr.text((18,15+i*32),line,font=f,fill='#14243c')
    canvas.save(FIG/name)


def schema(idx,name):
    h(name)
    rows=[]
    for row in old.tables[idx].rows[1:]:
        a=[c.text for c in row.cells];field=a[0].split()[-1]
        rows.append([field,a[1],a[2]+'；'+('可空' if a[3]=='是' else '非空'),('附件标识' if field == 'Attachment' else a[4])])
    table(['字段','类型','键和空值约束','说明'],rows,[3.4,3.6,3.6,6.0])

# 1 封面
for _ in range(3):p()
q=p('安全科学与工程学院',True);q.alignment=1;q.runs[0].font.size=Pt(22)
for text in ['2025 － 2026 学年第一学期','互联网应用服务开发与数据库实践']:
    q=p(text);q.alignment=1
p();q=D.add_paragraph('CTF训练竞赛平台系统设计报告','Title');q.alignment=1
p();p()
for text in ['题目：CTF训练竞赛平台的设计与实现','班级：24034202','学号：241240075','姓名：闫博泉','电子签（必填）：____________________','教师：邢艳','成绩：____________________']:
    q=p(text);q.paragraph_format.left_indent=Cm(2.1);q.paragraph_format.space_after=Pt(14)
p();q=p('2026 年 11 月 14 日');q.alignment=1
# 2 目录
page('目录')
contents=[('一 系统需求分析','3'),('二 系统总体设计','5'),('三 数据库设计','6'),('四 系统详细设计与实现','13'),('五 系统说明','22'),('六 课程设计总结','23'),('七 AI使用说明','23'),('八 版本控制记录','24')]
table(['章节','起始页'],contents,[14.2,2.4])
p('本报告说明 CTF 训练平台的需求、模块、数据库、应用实现与验证结果。系统已实现学生训练和管理员维护流程，数据库验证与应用测试结果可在源码目录逐项复现。')
p('提交材料包括本报告的 Word 和 PDF、可运行源代码、数据库初始化 SQL 与实际导出的备份 SQL。电子签由作者本人签署。')
h('阅读与复现位置')
table(['内容','对应文件'],[['应用入口','src/web/app.py'],['数据访问','src/web/db.py'],['数据库初始化','database/ctf_init.sql'],['导出备份','database/ctf_backup.sql'],['数据库验证','scripts/verify_db.py'],['应用集成测试','tests/test_web.py']],[5,11.6])
# 3
page('一 系统需求分析')
h('1.1 系统开发背景')
p('CTF 训练要求学生在 Pwn、Web、Reverse、Crypto 和 Misc 等方向反复练习，并通过提交 flag 验证结果。高校课程与社团的训练通常需要持续开放题库，学生的练习时间和进度并不一致。若由管理员人工登记提交和核算成绩，容易发生反馈延迟、重复计分以及总分与明细不一致的问题，也难以在考核时解释某一笔分数的来源。')
p('本系统将训练活动组织为题目录入、草稿维护、上架、浏览检索、提交判定、得分与排名的完整流程。题目上架之前不进入公共题库；每次提交均保留记录；仅首次正确提交形成解题计分。同一道题的后续正确提交反馈已解出且不再加分，后续错误提交仍如实记为错误。管理员可以查阅操作和积分日志，以复核状态变化及成绩。')
h('1.2 系统目标')
p('系统面向学生与训练管理员两类角色。学生使用网页完成注册登录、按方向和难度找题、提交答案以及查看个人成绩。管理员通过后台录入和修改题目、删除无提交草稿、控制题目上下架，并管理学生账号状态。核心计分规则由数据库存储过程统一实现，应用层负责输入校验、权限判断和结果展示，使业务行为可以直接测试与解释。')
p('开发目标是交付可在本机复现的课程演示系统：至少提供五类网页和十类控件，至少使用三个基本表，并实际使用视图、存储过程、触发器完成业务。报告、源码、数据库文件和版本历史相互对应，能够支持教师现场提问、运行演示及简单修改。')
h('用户及使用范围')
p('游客可浏览已上架题目和排行榜。学生登录后可提交 flag、修改邮箱和密码、查询个人记录。管理员可维护题目、启停学生账号和检索日志。本项目提供平台流程演示，不运行漏洞靶机；原始题目附件未纳入交付范围。')
# 4
page('1.3 功能需求与非功能需求')
table(['角色','功能','验收行为'],[['游客','注册、检索、查看排行','草稿与下线题目不可见'],['学生','提交、查分、查看明细','首次正确计分，重复不加分'],['学生','修改资料及密码','改密需验证当前密码'],['管理员','题目录入、修改、上架和下线','新增题目以草稿状态保存'],['管理员','删除草稿','有历史提交或非草稿则拒绝'],['管理员','账号状态及日志维护','学生不能进入后台']],[2.5,6,8.1])
h('1.4 非功能需求')
p('安全性方面，所有 SQL 值均使用参数绑定；客户端提交不能指定当前操作人的身份，身份从服务器校验后的会话读取。POST 请求校验 CSRF token，模板自动转义输出。密码和 flag 不以明文写入业务表，公共题库视图不返回 flag 散列。停用账号在下一次请求时失去会话权限。')
p('一致性方面，判题过程以事务包围提交和计分，联合主键约束同一用户同一题仅有一条计分。同一账号的提交先锁定用户行，再锁定题目行，保证并发提交产生的累计积分日志与得分总额一致。管理员修改或删除题目时也在事务内检查状态和提交记录。')
p('可用性方面，表单包含必填、长度与范围限制，服务端重复校验；错误通过页面明确反馈。页面使用统一导航与响应式网格，窄屏下改为单列。已验证 Chromium 的页面操作和 390 像素宽度布局；其他浏览器、长期稳定性和大规模负载未进行专项测试，因此不作为已达到的性能指标。')
# 5
page('二 系统总体设计')
p('系统采用 B/S 架构。浏览器提交 HTML 表单，Flask 路由验证请求后调用 MySQL；Jinja2 模板渲染查询和操作结果。训练判定及计分不在 JavaScript 中实现，浏览器不能自行决定得分。')
image('module.png','图1 系统功能模块图')
h('2.1 前台训练子系统')
p('注册、登录与个人中心管理学生身份；题库页面组合分类、难度和关键词查询；详情页提交 flag；排行榜与个人记录读取同一套计分数据，避免维护独立的累计分字段。')
h('2.2 后台管理及数据访问')
p('后台按管理员角色开放题目和账号维护。db.py 为每个请求建立独立连接，请求结束关闭连接。普通查询启用自动提交；由应用组成的多条修改语句使用显式事务；存储过程自行控制其事务。服务端只允许固定的过程名及输出参数名。')
# 6
page('三 数据库设计')
h('3.1 概念结构设计')
p('系统抽取用户、分类、题目、提交、解题计分、积分日志、操作日志七个实体。提交是每次作答的事实，解题计分是某用户首次解出某题的结果，两者分开保存。')
image('er.png','图2 系统实体联系图')
p('分类与题目为一对多，用户与提交、题目与提交均为一对多。用户与题目的解题关系由 Solves 表实现；每条计分关联首次正确提交。积分日志记录该次计分后的累计值，操作日志记录管理员状态变更和注册行为。')
# 7
page('3.2 逻辑结构设计')
rels=[('Users','Uid','Username, PasswordHash, Salt, Email, Role, Status, CreatedAt'),('Categories','Cid','Cname, Cdesc'),('Challenges','Chid','Cid, Title, Description, Difficulty, Score, FlagHash, FlagSalt, Attachment, Status, AuthorUid, CreatedAt, PublishedAt'),('Submissions','Subid','Uid, Chid, FlagHash, IsCorrect, SubmittedAt'),('Solves','Uid, Chid','Subid, ScoreAwarded, SolvedAt'),('ScoreLogs','LogId','Uid, Chid, DeltaScore, TotalAfter, Action, OccurredAt'),('OperationLogs','Opid','Uid, Action, Target, Detail, OccurredAt')]
for name,key,fields in rels:
    q=p();q.add_run(name+'（');q.add_run(key).underline=True;q.add_run(', '+fields+'）')
p('上述关系模式中，下划线字段为主键。Solves 的主键是联合主键，其 Subid 另有唯一约束；因此同一题不能重复计分，同一提交也不能被不同计分记录重复引用。')
h('完整性与历史保留规则')
p('数据库通过 10 个外键关联父子记录。已有提交的用户和题目受到引用完整性保护，不能直接删除。题目难度必须在 1 至 5，分值与计分必须大于零，提交正确性只能为 0 或 1。用户名、分类名使用唯一约束，防止重复实体。')
p('应用进一步限制题目的历史修改：产生提交后不再修改题名、分类、分值与 flag，以保证历史记录的解释稳定。描述、难度和附件标识允许更新。下线仅影响题库可见性，不清除已有成绩。')
# 8
page('3.3 物理结构设计 用户与分类')
p('数据库名为 ctf，表使用 InnoDB 和 utf8mb4。以下列出实际建表字段，完整注释与约束定义保存在初始化 SQL。')
schema(1,'用户表 Users');schema(2,'分类表 Categories')
p('学生与管理员共用用户表，以 Role 区分权限，以 Status 管理账号可用性。注册产生的盐随机生成，演示数据的固定口令仅用于复现。')
# 9
page('3.3 物理结构设计 题目')
schema(3,'题目表 Challenges')
p('Status 的 draft、online、offline 对应草稿、上架与下线。只有 online 记录进入公共视图。AuthorUid 保存录题人，PublishedAt 保存上架时间。FlagHash 与 FlagSalt 仅在判定过程内部使用。')
# 10
page('3.3 物理结构设计 提交和计分')
schema(4,'提交表 Submissions');schema(5,'计分表 Solves')
p('Submissions 保存每次尝试的散列、判定和时间，Solves 只保存首次成功的得分。排行榜对 Solves 聚合，不根据提交次数累计，因此不会因重复提交增加总分。')
# 11
page('3.3 物理结构设计 日志')
schema(6,'积分日志 ScoreLogs');schema(7,'操作日志 OperationLogs')
p('积分日志由解题计分触发器写入。操作日志记录注册、录题、上下架、修改和草稿删除等行为，管理员可按用户名和日期筛选最近记录。')
# 12
page('3.4 索引与数据库对象')
rows=[]
for r in old.tables[8].rows[1:]:rows.append([c.text for c in r.cells])
table(['索引','表','索引列','用途'],rows,[4.2,3,4.1,5.3])
p('复合索引服务于分类、难度与状态筛选和个人记录排序。题名使用包含关键词查询时，LIKE 前置通配符通常不能利用普通 B 树前缀索引；本演示题量较小，未声称该检索具备索引加速。')
table(['数据库对象','数量','业务职责'],[['基本表','7','实体和事实记录'],['视图','5','公共题库、个人记录和排行'],['存储过程','5','注册、录题、上架、判题、个人记录'],['触发器','3','注册、状态变化和积分留痕']],[5,2,9.6])
# 13
page('四 系统详细设计与实现')
h('4.1.1 视图实现')
p('公共题库视图封装分类关联和上架条件，并且不投影 flag 散列。以下为实际定义。')
code(cut('CREATE OR REPLACE VIEW v_challenge_public','-- ------------------------------------------------------------',sql))
table(['视图','用途'],[['v_submission_record','逐笔提交及该笔实际得分'],['v_score_detail','每道已解出题的计分明细'],['v_total_rank','按总分及达到成绩的时间排名'],['v_category_rank','按分类分区统计排名']],[6.1,10.5])
p('总分榜和分类榜从 Solves 汇总，使用 RANK 窗口函数。同分时按照最后一次解出时间排序；完全相同的排序键允许并列。初始化状态下共 9 人入榜，榜首 wujiu 为 900 分。')
# 14
page('4.1.2 存储过程实现')
table(['过程','用途'],[['sp_register_user','校验注册格式并写入加盐口令'],['sp_add_challenge','校验管理员身份，新增草稿'],['sp_publish_challenge','将题目转为上架并触发留痕'],['sp_submit_flag','判定、提交、首次计分的完整事务'],['sp_user_records','返回某用户的答题记录']],[6.2,10.4])
p('注册过程在库内校验输入并生成散列。下面给出完整定义；其余过程保存在初始化 SQL。判题过程先锁用户再锁题目，将提交、首次计分与日志写入同一事务，错误时回滚。')
block=cut('CREATE PROCEDURE sp_register_user','END proc//',sql)+'\nEND proc//'
block='\n'.join(line for line in block.splitlines() if line.strip() and not line.lstrip().startswith('--'))
code(block)
# 15
page('4.1.3 触发器与事务')
p('三个触发器分别在用户插入后记录注册、题目状态更新后记录上下架、解题计分插入后记录积分变动。下面给出积分触发器的完整定义。')
start=sql.index('CREATE TRIGGER trg_solves_after_insert');end=sql.index('END//',start)+len('END//')
code(sql[start:end])
p('同一用户的并发提交在用户行锁处串行，触发器读取到的此前累计值随事务一起前进。不同用户可独立提交；同一用户同一题的联合主键仍是最终的结构约束。管理员编辑和删除同样使用事务，先锁定题目，再核对是否存在提交，最后进行写入或拒绝。')
p('应用连接启用 autocommit，因此每次独立查询不会留下未结束事务。多语句维护流程显式 begin、commit 或 rollback；请求结束后关闭连接，避免复用 @operator_uid 等会话变量导致操作人混淆。')
# 16
page('4.2.1 注册登录与页面结构')
p('应用使用 Flask 路由、Jinja2 模板和原生 CSS/JavaScript。注册调用数据库过程，登录在服务端比对口令散列，并检查账号状态；会话只保存用户编号，每次请求重新读取角色和状态。')
image('web-login.png','图3 登录页面真实运行截图',15.8)
table(['页面','职责'],[['/register 与 /login','新建身份与登录校验'],['/challenges 与详情页','检索、题面展示、flag 提交'],['/profile 与 /ranking','个人资料、记录及积分排行'],['/admin/challenges 及维护页','录入、修改、删除、上下架'],['/admin/users 与 /admin/logs','账号状态与日志查询']],[7,9.6])
h('关键HTML CSS与JavaScript片段')
code('<input name="flag" minlength="6" maxlength="128"\n       placeholder="flag{...}" required autocomplete="off">\n.cards { display:grid;\n  grid-template-columns:repeat(3,minmax(0,1fr)); }\nif (!form.checkValidity()) {\n  event.preventDefault(); form.reportValidity(); return; }')
# 17
page('4.2.2 数据检索与结果展示')
p('题库检索同时支持方向、难度和题名关键词。公共视图保证只有上架题目被显示，条件值通过 %s 占位符绑定。下图展示 Welcome 关键词检索结果。')
image('web-search.png','图4 题库检索运行截图',15.6)
codeshot('code-search.png',"        rows = query('SELECT * FROM v_challenge_public WHERE", "        return render_template('challenges.html'")
image('code-search.png','图5 检索参数化查询源代码截图',16.2)
p('模板对题名和题面自动转义；恶意 HTML 不会作为标签执行。检索无结果时显示空状态，非法难度返回明确的请求错误。')
# 18
page('4.2.3 数据录入功能')
p('管理员填写题名、分类、难度、分值、flag 与题面。服务端重新检查数值和长度，并把当前会话身份作为操作人，调用 sp_add_challenge 保存为草稿。学生端不能执行该路由。')
image('web-create.png','图6 管理员录题页面',15.6)
codeshot('code-create.png',"            values = challenge_values()", "        return render_template('challenge_form.html', item=None")
image('code-create.png','图7 数据录入调用源代码截图',16.2)
p('难度采用 range 控件并实时更新 output，分值采用 number，题面使用 textarea。Flag 输入为 password 类型，既有控件校验，也有服务端长度校验和数据库散列存储。')
# 19
page('4.2.4 数据修改功能')
p('管理员进入修改页面更新题目信息。产生提交记录的题目不允许更改 flag、标题、分类和分值。个人中心修改密码则必须验证当前口令，成功后清除本次会话并要求重新登录。')
image('web-edit.png','图8 题目信息修改页面',15.6)
codeshot('code-edit.png',"                execute('UPDATE Challenges SET Cid=", "                db.commit()")
image('code-edit.png','图9 题目修改与操作留痕源代码截图',16.2)
# 20
page('4.2.5 数据删除与状态维护')
p('只有没有提交记录的草稿可删除。管理员按删除按钮后出现确认提示；服务端在事务中锁定题目，校验状态与提交记录，删除后写入操作日志。已有历史记录的题目使用下线处理。')
image('web-admin.png','图10 管理后台与删除入口',15.6)
codeshot('code-delete.png',"            if action == 'delete':", "            else:\n                execute('SET @operator_uid")
image('code-delete.png','图11 删除条件校验及写入源代码截图',16.2)
p('外键对提交和计分的引用形成第二层保护。状态变更由触发器自动留痕，下线后公共题目详情返回不可访问，原有成绩保留。')
# 21
page('4.2.6 交互安全与系统测试')
p('HTML 使用 form、input text、password、email、search、number、range、checkbox、select、textarea、button、details 和 output 等多类控件。CSS 使用网格和媒体查询；JavaScript 负责删除确认、合法性提示、提交按钮短暂禁用与难度读数更新，数据库继续承担最终计分约束。')
image('web-judge.png','图12 真实 flag 提交判定结果',13.8)
table(['验证内容','实际结果'],[['数据库对象、视图、过程与约束','MySQL '+verify['mysql_version']+'，29 项通过'],['Web 业务与安全','6 组集成测试通过'],['同一用户同一题 6 路并发','仅 1 次首次得分，另外 5 次不重复计分'],['同用户跨题与重复混合提交','积分日志累计值 200、300，合计一致'],['账号停用、CSRF 和学生后台访问','分别清除权限、拒绝表单、返回禁止访问']],[9.4,7.2])
p('数据库测试包含正常和异常路径；应用测试调用真实 MySQL。页面截图来自实际服务运行。验证原始输出见两个 verification.json，测试代码见 tests/test_web.py。')
# 22
page('五 系统说明')
h('5.1 开发与验证环境')
table(['组件','环境与用途'],[['应用','Python 3.12、Flask 3.1.3、PyMySQL 1.2.4'],['数据库','MySQL Community Server 8.4.7'],['界面','Jinja2、HTML5、原生 CSS 与 JavaScript'],['验证','unittest、Chromium 页面操作'],['文档','python-docx，Word 与 PDF 同源导出']],[4.3,12.3])
h('5.2 安装与运行')
code('python3 -m venv .venv\nsource .venv/bin/activate\npip install -r requirements.txt\nmysql -u root -p < database/ctf_init.sql')
p('为 ctf 库创建应用账号，在 .env.example 的副本 .env 中配置连接信息和随机会话密钥。按 README 导出环境变量，再运行 python src/web/app.py，打开 http://127.0.0.1:5000。该启动方式用于本机课程演示。')
h('5.3 演示与数据库恢复')
p('管理员使用 admin / Admin@123；学生使用 zhangsan / Pass@123。首次答题演示可使用 xuer / Pass@123，向 Welcome Pwn 提交 flag{w3lc0me_pwn}；错误提交不得分，重复正确提交不加分。')
p('ctf_backup.sql 由 mysqldump 实际导出，包含表、数据、过程和触发器。可使用 mysql -u root -p < database/ctf_backup.sql 恢复。初始化与验证会修改数据库，只在专用演示库操作。原始漏洞附件未交付，当前系统演示重点为平台流程。')
# 23
page('六 课程设计总结')
p('本次设计围绕训练平台完成了需求到实现的完整流程。数据库层将用户、分类、题目、提交、计分和日志拆分为七个关系，利用主键、唯一约束、外键和检查约束实现完整性；应用层提供注册登录、找题作答、个人记录、积分排行及后台维护。原先报告中的应用示例已落为可执行程序，并与数据库层通过参数化调用连接。')
p('主要难点是重复计分与并发行为。仅在应用中先查询再写入不能保证两个同时到达的请求都遵守规则，因此联合主键必须在结构层兜底。同一用户不同题并发时，累计日志也可能遇到先后次序问题；当前过程先锁定用户行，使该用户的积分变动按事务顺序完成。测试还发现已解出题目后的错误提交曾被标为正确，修复后记录反映实际判定，计分仍保持唯一。')
p('另一个难点是资料之间的一致性。数据库对象、应用代码、报告示例和备份必须反映同一实现，单独完成 SQL 并不能替代网页的增删改查。通过真实数据库集成测试、实际运行截图和 Git 提交，能够逐项检查功能是否落实。后续可补充题目附件和靶机部署、请求限流、更强的口令派生算法，以及真实浏览器兼容性和负载测试；这些内容不列为本次已完成成果。')
h('七 AI使用说明',1)
p('本项目使用 AI 辅助补全应用代码、检查数据库逻辑、编写测试和整理报告。新增代码及文档按实际改动提交，提交作者标识为 ChatGPT Codex；原始项目历史保留。作者本人应运行系统、阅读源码，理解数据流、事务、约束与权限判断，并在验收前练习现场修改。电子签和独立理解应由本人完成。')
# 24
page('八 版本控制记录')
p('远程仓库：https://github.com/GGBoss06/ctf-training-platform。代码与报告保存在同一 Git 项目；提交采用 feat、fix、test、docs 等前缀。下表为本报告编制时的真实历史，按时间由早到晚排列。新提交未改写既有历史，未回填日期。')
log=subprocess.check_output(['git','log','--reverse','--format=%h%x09%s'],cwd=ROOT,text=True).strip().splitlines()
rows=[]
for i,line in enumerate(log,1):
    key,msg=line.split('\t',1);rows.append([i,key,msg])
table(['序号','提交','实际改动'],rows,[1.4,2.5,12.7])
p('交付项目已包含不少于 20 次本地提交。新增提交需在本人 GitHub Desktop 中添加交付项目并点击 Push origin，同步完成后再在 GitHub 网页核对数量。仓库历史快照与电子签后的最终报告均应推送保存。')
D.core_properties.title='CTF训练竞赛平台系统设计报告'
D.core_properties.author='闫博泉'
D.core_properties.subject='互联网应用服务开发与数据库实践课程设计'
out=DOCS/'CTF训练竞赛平台系统设计报告.docx';D.save(out);print(out)
