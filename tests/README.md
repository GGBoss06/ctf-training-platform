# 集成测试

使用真正的 MySQL，覆盖页面、检索、CSRF、权限、注册、资料修改、题目增删改查、上下架、判题、重复提交、并发计分和账号停用。

先将初始化 SQL 导入专用演示库，配置连接变量，再执行：

```bash
CTF_RUN_INTEGRATION=1 python -m unittest discover -s tests -v
```

测试会写入数据。未设置开关时跳过。结果见 docs/web_verification.json。
