# CTF 训练竞赛平台

《互联网应用服务开发与数据库实践》课程设计。Flask + MySQL，实现学生训练与后台管理。报告学生信息沿用原始初稿：241240075 闫博泉，24034202 班。

## 已实现功能

- 注册、登录、退出、邮箱与密码修改。
- 分类、难度、关键词组合检索；题面查看与 flag 判定。
- 个人提交记录、得分明细、总分榜及分类榜。
- 管理员录题、修改、上架、下线、删除（已上架或已有提交的题目也可删除，相关提交与得分记录同步清理）、学生账号启停、账号管理（修改资料、重置密码、删除账号）、日志筛选。
- 7 张表、5 个视图、5 个存储过程、3 个触发器。
- CSRF、服务端角色与账号状态检查、参数化 SQL、页面输出转义。

演示包包含题面和演示 flag，不包含原始漏洞练习附件；附件字段仅记录标识，页面不提供失效下载按钮。
数据库保留课程已有的 SHA-256 加盐口令设计；正式系统应迁移到专门的口令哈希算法，并增加限流与部署加固。

## 本机运行

需要 Python 3.11 或 3.12、MySQL 8.0.16 以上（推荐 8.4）。以下命令在项目目录执行。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mysql -h 127.0.0.1 -u root -p < database/ctf_init.sql
```

初始化脚本用于全新数据库。随后以管理员登录 MySQL，单独创建应用账号：

```sql
CREATE USER 'ctf_app'@'localhost' IDENTIFIED BY '自行设置数据库密码';
GRANT SELECT,INSERT,UPDATE,DELETE,EXECUTE ON ctf.* TO 'ctf_app'@'localhost';
```

复制 `.env.example` 为 `.env`，填写数据库密码，把 `CTF_SECRET_KEY` 改成随机字符串。`.env` 已被 Git 忽略。

```bash
cp .env.example .env
# 使用编辑器填写 .env，完成后执行：
set -a
source .env
set +a
python src/web/app.py
```

打开 http://127.0.0.1:5000 。管理员 `admin / Admin@123`；学生 `zhangsan / Pass@123`。未解题学生 `xuer / Pass@123` 可验证首次得分。
演示题 Welcome Pwn 的 flag 为 `flag{w3lc0me_pwn}`；SQL 注入初探为 `flag{sql_1nj3ct10n}`。这些均为公开测试数据。

## 数据库恢复

- `database/ctf_init.sql`：结构、视图、过程、触发器及初始数据。
- `database/ctf_backup.sql`：由 MySQL 8.4.7 的 mysqldump 实际导出，含 routines、triggers、events 和初始数据。

```bash
mysql -h 127.0.0.1 -u root -p < database/ctf_backup.sql
```

备份含 DEFINER 信息，建议由有创建存储过程和触发器权限的本机数据库管理员导入。

## 验证

`docs/db_verification.json` 为 29 项数据库验证结果；`docs/web_verification.json` 为 7 组应用集成测试结果。数据库验证会重建 `ctf` 库，集成测试会写入账号和记录；只连接专用演示库。

```bash
export CTF_DB_USER=root
export CTF_DB_PASSWORD='本机测试数据库密码'
python scripts/verify_db.py
CTF_RUN_INTEGRATION=1 python -m unittest discover -s tests -v
```

Windows PowerShell 可使用 `$env:CTF_DB_USER='root'` 等设置同名环境变量。

## 目录

- `src/web/`：应用全部源码。
- `database/`：初始化和导出 SQL。
- `docs/`：报告、验证结果与真实运行截图。
- `scripts/`：验证和文档生成工具。
- `tests/`：业务、权限及并发集成测试。

旧初稿和旧生成脚本保留作历史材料，验收以最终报告为准。

## GitHub Desktop 同步

远程仓库：https://github.com/GGBoss06/ctf-training-platform

交付项目保留 `.git` 目录。新增提交对应实际代码、测试和报告改动，原始历史未改写，未回填日期。

1. 解压交付包，打开 GitHub Desktop。
2. 选择 **File → Add Local Repository**，定位 `02_程序源代码/ctf-training-platform`。
3. 确认仓库为 `GGBoss06/ctf-training-platform`、分支为 `main`。
4. 点击 **Push origin**，等待完成。在 GitHub 网页核对提交总数至少 20。
5. 若远程已有新提交，先保留双方材料并处理合并，不要强制推送。

## 电子签

Word 与 PDF 采用同一报告。电子签栏需本人签署；在 Word 插入本人签名后，重新导出 PDF，再通过 GitHub Desktop 提交并推送两份报告。
