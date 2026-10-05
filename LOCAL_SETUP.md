# 本地修复版

已过滤登录快照中的浏览器管理请求头（大小写不敏感，支持 Sec-Fetch / Sec-CH-UA 前缀），默认使用 Playwright Chromium，并删除调试收尾的 input()。
显式 LOGIN_IS_EDGE=true 仍会使用本机 Edge。浏览器选择不保证规避平台风控。

## 启动

双击 run-local.command，或在项目目录执行 `./run-local.command`。
默认访问 http://127.0.0.1:8000；修改 .env 中 SERVER_PORT 后，启动脚本会使用对应端口。默认账号 admin，密码 admin123。
关闭终端或按 Ctrl+C 停止服务。

## 填写配置

首次克隆后执行 `cp .env.example .env`，填写自己的模型配置和 API Key。`.env` 不随仓库发布。
如需复现教程中的方舟配置，可在 `.env` 中设置：

```ini
OPENAI_API_KEY=替换为自己的Key
OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/plan/v3
OPENAI_MODEL_NAME=doubao-seed-2-0-pro-260215
ENABLE_RESPONSE_FORMAT=false
RUN_HEADLESS=true
```

以上服务地址和模型名来自教程，未经过真实 API 验证；订阅权限、可用模型和结构化输出支持以实际账号为准。
在账号管理导入你自己的闲鱼登录态，然后创建任务并绑定账号。API Key 与登录态不应提交到 Git。
未提供这些凭据，因此尚未验证真实商品抓取、AI 分析及落库的完整链路。

## 环境重建

```sh
cp .env.example .env  # 仅首次配置，已有 .env 时不要覆盖
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python -m playwright install chromium
(cd web-ui && npm ci && npm run build)
./run-local.command
```

## 回归检查

```sh
.venv/bin/python -m pytest tests/unit/test_scraper_browser_channel.py
```

## 本次 bug 检查

- 本地启动器读取 SERVER_PORT，不再固定 8000。
- start.sh 优先使用项目虚拟环境，支持 uv 安装的无 pip 环境；先安装 Python 依赖，再安装匹配版本的 Chromium。
- 后台分析异常保留到 join() 上报，等待其他任务完成，不再丢失提前结束任务的异常。
- 保存失败会报告失败，不发送未落库商品的推荐通知。
- 后台分析收尾失败时仍执行 browser.close()。
- 更新过时的 Docker 构建路径配置及 SQLite 结果元数据测试预期。

验证：120 项离线测试通过，3 项真实服务测试未运行；自定义端口、无标准输入条件下的实际启动与页面 HTTP 200 检查通过。真实闲鱼和 AI 调用仍需登录态及 API Key。
