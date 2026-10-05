# 修改说明

基于 Usagi-org/ai-goofish-monitor 的 `f85d140`，保留原项目 MIT 许可证。

## 修复内容

| 问题 | 修改后的行为 |
| --- | --- |
| 登录快照的旧请求头被传给新的浏览器请求 | 过滤 Cookie、Origin、Referer、User-Agent、正文相关头，以及 Sec-Fetch-*、Sec-CH-UA* 等浏览器管理字段；匹配不区分大小写，保留业务自定义头 |
| 本地默认依赖系统 Chrome | 默认使用 Playwright 安装的 Chromium；显式选择 Edge 和 Docker 使用 Chromium 的行为保留 |
| 调试任务在后台执行 input() 导致 EOFError 或阻塞 | 移除等待键盘输入，自动关闭浏览器 |
| 已结束的后台分析任务被移出集合，异常可能漏报 | 收集首个失败，join() 等待其他任务结束后上报 |
| 商品写入失败仍发送推荐通知 | 写入失败抛出异常，不增加完成数，不发送该商品的通知 |
| 分析收尾异常跳过 browser.close() | 使用 finally 执行浏览器关闭 |
| 本地启动端口写死为 8000 | run-local.command 读取 SERVER_PORT，并仅绑定 127.0.0.1 |
| start.sh 使用系统 Python，依赖检查早于安装 | 优先激活项目 .venv，兼容 uv 创建的无 pip 环境，安装依赖后下载匹配的 Chromium |

另更新 Docker 忽略文件中过时的前端构建路径，以及 SQLite 结果附加状态字段的测试预期。忽略虚拟环境、前端依赖和工作日志，避免纳入版本控制。

## 配置与运行

参见 [LOCAL_SETUP.md](LOCAL_SETUP.md)。不包含真实 API Key、闲鱼登录态、数据库或抓取结果；新克隆需要自行创建 `.env` 并安装依赖。

本次实际部署是 macOS 本地部署。默认 `docker-compose.yaml` 使用上游预构建镜像，不包含本分支修改；如后续要测试本分支的 Docker 构建，应使用仓库提供的 `docker-compose.dev.yaml`（`docker compose -f docker-compose.dev.yaml up --build -d`）。Docker 路径本次未实测。

## 验证结果

- Python 3.11.14，macOS。
- `python -m pytest -m 'not live'`：120 项通过，3 项真实服务测试排除。
- 前端 `npm ci && npm run build` 成功。
- Playwright Chromium 无头启动、创建页面、关闭成功。
- 自定义端口且标准输入关闭时，实际启动脚本可以启动服务，管理页面返回 HTTP 200。
- `bash -n start.sh run-local.command` 与 `git diff --check` 通过。

未提供真实闲鱼登录态和模型 API Key，未验证真实搜索、AI 分析、商品落库全链路；浏览器和请求头修改不保证平台风控放行。教程中的方舟地址和模型配置仅作为示例，不代表当前订阅可用性保证。
