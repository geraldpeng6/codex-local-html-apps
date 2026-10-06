# Codex HTML 应用台插件

一个基于 [MCP Apps](https://developers.openai.com/plugins/build/chatgpt-ui) 的本地 Codex 插件。同一个 MCP server 按需返回多个 HTML UI：预置贪吃蛇、扫雷、股票行情和加密货币行情；新增页面只需要在 `apps/` 放 HTML，并在 `server.py` 注册。

## 应用

| 应用 | 数据来源 | 说明 |
| --- | --- | --- |
| HTML 应用台 | 本地 | 预置应用入口 |
| 贪吃蛇 | 本地 | 键盘/触屏、暂停、重开和最高分 |
| 扫雷 | 本地 | 三档难度、安全首击、插旗、计时 |
| 股票行情 | 腾讯公开行情 | 支持名称搜索，以及美股、港股、A股和指数代码 |
| 加密货币 | Binance | 六个预设交易对、10 秒刷新、可暂停 |

游戏页面离线可用；行情页需要浏览器能访问对应公开 API。股票页使用腾讯行情接口，接口公开且带 CORS `*`，但数据质量和可用性仍以实时接口为准。

## 本地安装

本仓库自带 `.agents/plugins/marketplace.json`。执行：

```sh
codex plugin marketplace add /absolute/path/to/local-html-apps --json
codex plugin add local-html-apps@local-html-apps --json
```

MCP 配置使用插件内相对路径 `./server.py`；这是 Codex 插件加载器要求的 bare executable 或 contained `./` path。安装器会缓存文件，修改源代码后需要重新安装并重启 Codex。

## 添加应用

1. 把独立 HTML 放进 `apps/`。
2. 在 `server.py` 的 `APPS_INDEX` 加一项，指定 slug、标题、文件名、工具描述、返回文案；访问外部 API 时设置 `connect_domains`。
3. 升级 `plugin.json` 的版本号，重新安装插件。

工具通过 `_meta.ui.resourceUri` 关联自己的 `ui://local-html-apps/<file>` 资源，并声明 `global` 和 `thread` 入口。
