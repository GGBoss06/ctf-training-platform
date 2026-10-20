# 应用层（规划中）

B/S 架构前台训练子系统与后台管理子系统，页面清单：

| 页面 | 功能 | 依赖对象 |
|---|---|---|
| 注册 / 登录 | 账号注册与登录校验 | sp_register_user、Users |
| 题库列表 | 按分类与难度检索题目 | v_challenge_public |
| 题目详情 | 查看题面、下载附件、提交 flag | sp_submit_flag、Challenges |
| 个人中心 | 答题记录与得分明细 | sp_user_records、v_submission_record |
| 排行榜 | 总分榜与分类榜 | v_total_rank、v_category_rank |
| 后台录题 / 上架 | 题目录入与上架 | sp_add_challenge、sp_publish_challenge |
| 审计日志 | 关键操作查询 | OperationLogs、ScoreLogs |

数据库访问统一使用参数化查询，连接参数：database=ctf、charset=utf8mb4、autocommit=False。
