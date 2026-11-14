"""保留 Git 历史，按学号姓名生成课程交付 ZIP。"""
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent/'output'
NAME = '241240075闫博泉'
TARGET = OUT/NAME
if TARGET.exists():
    shutil.rmtree(TARGET)
(TARGET/'01_系统设计报告').mkdir(parents=True)
(TARGET/'03_数据库文件').mkdir()
for suffix in ['docx','pdf']:
    name='CTF训练竞赛平台系统设计报告.'+suffix
    shutil.copy2(ROOT/'docs'/name,TARGET/'01_系统设计报告'/name)
for name in ['ctf_init.sql','ctf_backup.sql','README.md']:
    shutil.copy2(ROOT/'database'/name,TARGET/'03_数据库文件'/name)
shutil.copytree(ROOT,TARGET/'02_程序源代码'/'ctf-training-platform',
                ignore=shutil.ignore_patterns('rendered','rendered-*','__pycache__','*.pyc','.venv','.env','*.sock','*.log'))
shutil.copy2(ROOT/'docs'/'交付前检查.txt',TARGET/'提交前必读.txt')
history=subprocess.check_output(['git','log','--reverse','--format=%h %ad %an %s','--date=iso-strict'],cwd=ROOT,text=True)
count=subprocess.check_output(['git','rev-list','--count','HEAD'],cwd=ROOT,text=True).strip()
(TARGET/'04_版本控制记录.txt').write_text('本地真实提交总数：'+count+'\n远程同步需由本人在 GitHub Desktop 点击 Push origin。\n\n'+history)
archive=OUT/(NAME+'.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=8) as z:
    for f in sorted(TARGET.rglob('*')):
        if f.is_file():z.write(f,f.relative_to(OUT))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
print(archive)
print('commits='+count+'; bytes='+str(archive.stat().st_size))
