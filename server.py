#!/usr/bin/env python3
"""Local HTML MCP App plugin. Python standard library only."""

import base64
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
APPS = ROOT / "apps"
VERSION = "1.1.2"
PROTOCOLS = ("2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25", "2026-07-28")

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="none"><path d="M4 15h8a3 3 0 0 0 0-6H7a3 3 0 0 1 0-6h7v3" stroke="currentColor" stroke-width="1.33" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="4.5" r=".7" fill="currentColor"/></svg>'
ICON = "data:image/svg+xml;base64," + base64.b64encode(SVG.encode()).decode()
ICONS = [{"src": ICON, "mimeType": "image/svg+xml"}]


class App:
    def __init__(self, slug, title, filename, description, result_text, connect_domains=()):
        self.slug = slug
        self.title = title
        self.filename = filename
        self.description = description
        self.result_text = result_text
        self.uri = f"ui://local-html-apps/{filename}"
        self.mime = "text/html;profile=mcp-app"
        self.connect_domains = list(connect_domains)

    @property
    def resource(self):
        return {
            "uri": self.uri,
            "name": f"{self.slug}-ui",
            "title": self.title,
            "mimeType": self.mime,
        }

    @property
    def tool(self):
        return {
            "name": f"{self.slug}.open",
            "title": self.title,
            "description": self.description,
            "icons": ICONS,
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": bool(self.connect_domains)},
            "_meta": {
                "ui": {"resourceUri": self.uri},
                "openai/ui": {"entrypoints": [{"type": "global"}, {"type": "thread"}]},
            },
        }

    def read(self):
        csp = {"connectDomains": self.connect_domains, "resourceDomains": []}
        return {
            "uri": self.uri,
            "mimeType": self.mime,
            "text": (APPS / self.filename).read_text(encoding="utf-8"),
            "_meta": {"ui": {"prefersBorder": False, "csp": csp}},
        }


APPS_INDEX = {
    "apps": App(
        "apps",
        "HTML 应用台",
        "loader.html",
        "打开预置应用入口，选择游戏或行情面板。",
        "HTML 应用台已准备好。可选择贪吃蛇、扫雷、股票行情或加密货币。",
    ),
    "snake": App(
        "snake",
        "贪吃蛇",
        "snake.html",
        "打开可玩的贪吃蛇游戏，支持键盘、触屏和最高分。",
        "贪吃蛇已准备好。方向键或 WASD 转向，空格暂停，R 重开。",
    ),
    "minesweeper": App(
        "minesweeper",
        "扫雷",
        "minesweeper.html",
        "打开扫雷，支持三档难度、安全首击、插旗和计时。",
        "扫雷已准备好。左键翻开，右键或长按插旗。",
    ),
    "stocks": App(
        "stocks",
        "股票行情",
        "stocks.html",
        "查看美股、港股、A股和指数行情，支持名称或代码搜索。",
        "股票行情已准备好。默认读取腾讯公开行情；可添加或移除关注标的。",
        ("https://qt.gtimg.cn", "https://web.ifzq.gtimg.cn", "https://smartbox.gtimg.cn"),
    ),
    "crypto": App(
        "crypto",
        "加密货币",
        "crypto.html",
        "查看 Binance 现货 24 小时行情，支持自动刷新和暂停。",
        "加密货币行情已准备好。默认包含 BTC、ETH、SOL、BNB、XRP 和 DOGE。",
        ("https://api.binance.com",),
    ),
}
TOOL_TO_APP = {f"{slug}.open": slug for slug in APPS_INDEX}


class InvalidRequest(ValueError):
    pass


def dispatch(method, params):
    if method == "initialize":
        requested = params.get("protocolVersion")
        version = requested if requested in PROTOCOLS else "2025-11-25"
        return {
            "protocolVersion": version,
            "capabilities": {"tools": {}, "resources": {}},
            "serverInfo": {
                "name": "local-html-apps",
                "title": "HTML 应用台",
                "version": VERSION,
                "icons": ICONS,
            },
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": [app.tool for app in APPS_INDEX.values()]}
    if method == "tools/call":
        name = params.get("name")
        if name not in TOOL_TO_APP:
            raise LookupError("Unknown tool")
        if params.get("arguments") not in (None, {}):
            raise ValueError(f"{name}.open accepts empty arguments only")
        app = APPS_INDEX[TOOL_TO_APP[name]]
        return {
            "content": [{"type": "text", "text": app.result_text}],
            "structuredContent": {
                "app": app.slug,
                "title": app.title,
                "resourceUri": app.uri,
                "version": VERSION,
            },
        }
    if method == "resources/list":
        return {"resources": [app.resource for app in APPS_INDEX.values()]}
    if method == "resources/templates/list":
        return {"resourceTemplates": []}
    if method == "resources/read":
        uri = params.get("uri")
        matches = [app for app in APPS_INDEX.values() if app.uri == uri]
        if not matches:
            raise LookupError("Unknown resource")
        return {"contents": [matches[0].read()]}
    raise NotImplementedError("Unknown method")


def main():
    for line in sys.stdin:
        message = None
        try:
            message = json.loads(line)
            if (
                not isinstance(message, dict)
                or message.get("jsonrpc") != "2.0"
                or not isinstance(message.get("method"), str)
                or (
                    "id" in message
                    and (
                        isinstance(message["id"], bool)
                        or not isinstance(message["id"], (str, int, float, type(None)))
                    )
                )
            ):
                raise InvalidRequest("Invalid JSON-RPC request")
            if "id" not in message:
                continue
            params = message.get("params", {})
            if not isinstance(params, dict):
                raise ValueError("Expected object params")
            result = dispatch(message["method"], params)
            reply = {"jsonrpc": "2.0", "id": message["id"], "result": result}
        except Exception as error:
            code = (
                -32700
                if isinstance(error, json.JSONDecodeError)
                else -32600
                if isinstance(error, InvalidRequest)
                else -32601
                if isinstance(error, NotImplementedError)
                else -32602
                if isinstance(error, (LookupError, ValueError))
                else -32603
            )
            reply = {
                "jsonrpc": "2.0",
                "id": message.get("id") if isinstance(message, dict) and code != -32600 else None,
                "error": {"code": code, "message": str(error)},
            }
        sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
