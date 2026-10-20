# CTF 训练竞赛平台（CTF Training Platform）

《互联网应用服务开发与数据库实践》课程大作业
题目：**CTF训练竞赛平台的设计与实现**

## 项目简介

平台面向高校 CTF 队伍的日常训练与校内选拔场景，服务参赛学生（student）与训练管理员（admin）两类角色。
学生注册登录后可分类检索题目、查看详情并提交 flag，系统调用数据库存储过程在同一事务内完成查重、比对与计分，
即时返回判定结果与得分；个人中心可查看答题记录与得分明细；总分榜与分类榜实时展示训练排名。
管理员负责录题与上架，题目上架后进入公共题库。关键操作（注册、题目状态变更、积分变动）由触发器自动留痕。

数据库层是本项目的实现重点：7 张基本表、5 个视图、5 个存储过程、3 个触发器，全部脚本可在 MySQL 8.0+ 上一次性初始化并自动验证。

## 仓库地址

<https://github.com/GGBoss06/ctf-training-platform>

```bash
git clone https://github.com/GGBoss06/ctf-training-platform.git
```

## 目录结构

```
ctf-training-platform/
├── README.md                 项目说明（本文件）
├── .gitignore                忽略规则
├── docs/                                 文档与验证证据
│   ├── 系统设计文档_初稿.docx            大作业报告初稿（课程模板一至八章）
│   ├── CTF训练竞赛平台数据库实现说明.docx 数据库实现说明
│   ├── db_verification.json              数据库自动化验证结果（29 项）
│   └── figures/                          插图和版本控制记录截图
├── database/                             数据库脚本
│   ├── README.md                         脚本说明
│   └── ctf_init.sql                      建库建表 + 视图 + 存储过程 + 触发器 + 演示数据
├── scripts/                              工具脚本
│   ├── verify_db.py                      数据库自动化验证
│   ├── build_report.py                   数据库实现说明生成
│   ├── build_design_doc.py               系统设计文档生成
│   ├── build_figures.py                  功能模块图与 E-R 图生成
│   └── render_screenshot.py              版本控制记录截图生成
├── src/                      源代码
│   └── web/                  应用层（ASP.NET Web Forms，规划中）
└── tests/                    测试说明与用例
```

## 技术栈与环境

| 项目 | 说明 |
|---|---|
| 数据库 | MySQL 8.0+（字符集 utf8mb4，存储引擎 InnoDB） |
| 验证脚本 | Python 3.10+、PyMySQL |
| 报告生成 | Python 3.10+、python-docx |
| 应用层 | B/S 架构，前端与服务端见 `src/web`（规划中） |

## 快速开始

```bash
# 1. 初始化数据库（需先启动 MySQL 实例）
mysql -h 127.0.0.1 -P 3306 -u root -p < database/ctf_init.sql

# 2. 运行数据库自动化验证（会自动重建 ctf 库并导入脚本）
#    网络连接默认 127.0.0.1:3306，可用 CTF_DB_* 环境变量覆盖
python3 scripts/verify_db.py
#    或走 socket：CTF_DB_SOCK=/path/to/mysql.sock python3 scripts/verify_db.py

# 3. 重新生成报告（可选）
python3 scripts/build_report.py
```

演示账号：管理员 `admin / Admin@123`；学生 `zhangsan / Pass@123` 等。

## 提交规范

提交信息遵循 Conventional Commits：`<类型>(<范围>): <简述>`，类型取
`feat` / `fix` / `docs` / `style` / `refactor` / `test` / `build` / `chore`。

示例：

```
chore: 初始化项目仓库与标准目录结构
feat(database): 添加数据库初始化脚本
test(database): 添加数据库自动化验证
docs: 提交大作业报告初稿
```

## 作者信息

- 班级：24034202
- 学号：241240075
- 姓名：闫博泉
- 教师：邢艳
