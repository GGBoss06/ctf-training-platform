# 数据库脚本

## ctf_init.sql

一次性初始化脚本，包含：

- 建库：`ctf`，字符集 utf8mb4，存储引擎 InnoDB
- 7 张基本表：Users、Categories、Challenges、Submissions、Solves、ScoreLogs、OperationLogs
- 5 个视图：v_challenge_public、v_submission_record、v_score_detail、v_total_rank、v_category_rank
- 5 个存储过程：sp_register_user、sp_add_challenge、sp_publish_challenge、sp_submit_flag、sp_user_records
- 3 个触发器：注册留痕、题目状态变更留痕、积分变动留痕
- 演示数据：11 个账号、5 个分类、16 道题（上架 13）、28 次提交、22 条解题计分

## 执行

```bash
mysql -h 127.0.0.1 -P 3306 -u root -p < ctf_init.sql
```

脚本面向全新环境的一次性初始化。已有数据的库需要升级时，重新执行视图、存储过程与触发器定义即可，表内数据不受影响。
