# Web 应用

Flask + Jinja2 + 原生 HTML/CSS/JavaScript，连接 MySQL。包含登录、注册、题库、详情、个人中心、排行榜、题目管理、录题、修改、用户管理、日志等 11 类页面。

本实现取代旧初稿中未完成的 ASP.NET 示例；判定和计分仍由 MySQL 存储过程与触发器完成。

- app.py：路由、校验、会话、权限、CSRF。
- db.py：每请求连接、参数化查询、存储过程调用。
- templates/：Jinja2 页面。
- static/：样式与前端交互。

运行步骤见根目录 README。
