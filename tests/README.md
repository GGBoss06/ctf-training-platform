# 测试

数据库层的自动化验证位于 `scripts/verify_db.py`，覆盖 29 项断言：

- 初始数据规模与对象数量
- 视图输出列与排行榜数据一致性
- 存储过程正常与异常路径（注册、录题、上架、flag 判定、个人记录）
- 触发器自动留痕与积分累计一致性
- 主键、唯一、外键、CHECK 约束的拒绝行为
- 事务回滚无残留

```bash
python3 scripts/verify_db.py
```

结果写入 `docs/db_verification.json`。
