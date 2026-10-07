# Codex HTML 应用台插件

一个基于 [MCP Apps](https://developers.openai.com/plugins/build/chatgpt-ui) 的通用 HTML 运行时插件。`apps.open` 是唯一用户入口，页面顶栏可选择已注册应用；`runtime.load` 是内部加载协议。

## 应用

| 应用 | 数据来源 | 说明 |
| --- | --- | --- |
| HTML 应用台 | 本地 | 预置应用入口 |
| 贪吃蛇 | 本地 | 键盘/触屏、暂停、重开和最高分 |
| 扫雷 | 本地 | 三档难度、安全首击、插旗、计时 |
| 股票行情 | 腾讯公开行情 | 支持常见名称，以及美股、港股、A股和指数代码 |
| 加密货币 | Binance | 六个预设交易对、10 秒刷新、可暂停 |

游戏页面离线可用；行情页需要浏览器能访问对应公开 API。股票页按 GB18030 解码腾讯行情；常见名称在本地映射为代码，其余请填写完整代码。请求超时或失败会显示错误，数据可用性以接口实时返回为准。

## 本地安装

本仓库自带 `.agents/plugins/marketplace.json`。执行：

```sh
codex plugin marketplace add /absolute/path/to/local-html-apps --json
codex plugin add local-html-apps@local-html-apps --json
```

需要 Python 3.9+，无第三方运行依赖。MCP 配置使用插件内相对路径 `./server.py`。安装器会缓存文件，修改源代码后升级版本并重新安装。UI 资源地址包含服务器版本，更新时关闭旧页面，再从插件入口打开，核对顶栏版本；运行中的旧 MCP 连接可能仍需重启 Codex 才会更换。

## 添加应用

1. 把自包含 HTML 放进 `apps/`。
2. 在 `apps/app.json` 的 `apps` 数组加一项：`id`、`title`、`description`、`file`、`order`；访问外部 API 时设置 `connectDomains`。
3. 同步升级 `plugin.json` 和 `server.py` 的 `VERSION`，重新安装插件。

服务器把所有预置 HTML 安全地打包进应用台；列表和切换不依赖额外工具调用。运行时把选中页面放进单独 iframe，切换或返回列表会销毁旧 iframe。HTML 只需编写自己的界面，不需要包含 MCP 初始化代码。预置页面可以保存本地分数；通过“打开 HTML”导入的文件使用隔离来源，只在本次页面中保留。

“打开 HTML”支持单个自包含 `.html` / `.htm` 文件。它在本地浏览器读取文件，不上传或写入仓库；相对路径的图片、脚本和样式不会随文件导入。网络权限由插件资源的 CSP 决定，运行时导入不会自动增加权限。

应用台汇总清单中的 `connectDomains` 作为接口白名单。外部 iframe URL 默认不可用；预置页面通过 `srcdoc` 载入本地 HTML。

MCP 只暴露 `apps.open`（带 `global` 和 `thread` 入口）和 `runtime.load`（内部加载）。没有每个 HTML 的独立工具、UI 资源或深链接。

## 发布前检查

应在实际浏览器中确认四个预置选项、贪吃蛇开始/暂停、扫雷安全首击、行情数据或明确的错误、返回列表、来回切换，以及本地 HTML 脚本执行。还需验证 `ui/initialize` 请求包含 JSON-RPC `id`、宿主收到 initialized 通知；只检查 MCP 返回了 HTML 字符串不能证明 UI 正常。
