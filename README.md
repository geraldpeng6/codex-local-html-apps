# Codex HTML 应用台插件

一个基于 [MCP Apps](https://developers.openai.com/plugins/build/chatgpt-ui) 的通用 HTML 运行时插件。`apps.open` 打开唯一入口，页面顶栏可选择已注册应用；每个应用仍能通过独立工具或深链接直接打开。

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

1. 把自包含 HTML 放进 `apps/`。
2. 在 `apps/app.json` 的 `apps` 数组加一项：`id`、`title`、`description`、`file`、`order`；访问外部 API 时设置 `connectDomains`。
3. 升级 `plugin.json` 的版本号，重新安装插件。

通用运行时通过 `runtime.load` 按需取回 HTML，并放进独立 iframe。这样不需要为每个页面新增 server 代码。

工具通过 `_meta.ui.resourceUri` 关联自己的 `ui://local-html-apps/<file>` 资源，并声明 `global` 和 `thread` 入口。
