#!/usr/bin/env python3
"""Local HTML MCP App plugin. Python standard library only."""

import base64
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
APPS = ROOT / "apps"
MANIFEST = APPS / "app.json"
VERSION = "1.3.0"
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

    def read(self):
        csp = {"connectDomains": self.connect_domains, "resourceDomains": []}
        return {
            "uri": self.uri,
            "mimeType": self.mime,
            "text": (APPS / self.filename).read_text(encoding="utf-8"),
            "_meta": {"ui": {"prefersBorder": False, "csp": csp}},
        }

    @property
    def resource(self):
        return {
            "uri": self.uri,
            "name": "app-loader-ui",
            "title": self.title,
            "mimeType": self.mime,
        }


def load_manifest():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    apps = {}
    for item in data.get("apps", []):
        apps[item["id"]] = App(
            item["id"],
            item["title"],
            item["file"],
            item.get("description", ""),
            f"{item['title']}已准备好。",
            item.get("connectDomains", ()),
        )
    return apps


APPS_INDEX = load_manifest()
LOADER = App("apps", "HTML 应用台", "loader.html", "通用 HTML 应用运行时。", "HTML 应用台已准备好。")
LOADER_URI = "ui://local-html-apps/loader.html"


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
        tools = [
            {
                "name": "apps.open",
                "title": "HTML 应用台",
                "description": "打开通用 HTML 应用运行时，可在顶栏选择预置应用。",
                "icons": ICONS,
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
                "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": True},
                "_meta": {
                    "ui": {"resourceUri": LOADER_URI},
                    "openai/ui": {"entrypoints": [{"type": "global"}, {"type": "thread"}]},
                },
            }
        ]
        tools.append(
            {
                "name": "runtime.load",
                "title": "Load HTML App",
                "description": "Load one registered HTML app into the generic runtime. Used by apps.open.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"appId": {"type": "string", "description": "Registered app id from apps/app.json"}},
                    "required": ["appId"],
                    "additionalProperties": False,
                },
                "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": True},
            }
        )
        return {"tools": tools}
    if method == "tools/call":
        name = params.get("name")
        if name == "apps.open":
            if params.get("arguments") not in (None, {}):
                raise ValueError("apps.open accepts empty arguments only")
            return {
                "content": [{"type": "text", "text": LOADER.result_text}],
                "structuredContent": {"app": "apps", "title": LOADER.title, "version": VERSION},
            }
        if name == "runtime.load":
            arguments = params.get("arguments") or {}
            if not isinstance(arguments, dict) or set(arguments) - {"appId"}:
                raise ValueError("runtime.load accepts appId only")
            app_id = arguments.get("appId")
            if app_id == "__manifest__":
                apps = [
                    {
                        "id": app.slug,
                        "title": app.title,
                        "description": app.description,
                        "file": app.filename,
                        "connectDomains": app.connect_domains,
                    }
                    for app in APPS_INDEX.values()
                    if app.slug != "loader-preview"
                ]
                return {
                    "content": [{"type": "text", "text": f"已返回 {len(apps)} 个应用。"}],
                    "structuredContent": {"apps": apps, "version": VERSION},
                }
            if app_id not in APPS_INDEX or app_id == "loader-preview":
                raise LookupError("Unknown app")
            app = APPS_INDEX[app_id]
            return {
                "content": [{"type": "text", "text": f"已返回 {app.title} HTML。"}],
                "structuredContent": {
                    "appId": app.slug,
                    "title": app.title,
                    "html": (APPS / app.filename).read_text(encoding="utf-8"),
                    "connectDomains": app.connect_domains,
                },
            }
        raise LookupError("Unknown tool")
    if method == "resources/list":
        return {"resources": [LOADER.resource]}
    if method == "resources/templates/list":
        return {"resourceTemplates": []}
    if method == "resources/read":
        uri = params.get("uri")
        if uri == LOADER_URI:
            return {"contents": [LOADER.read()]}
        raise LookupError("Unknown resource")
    if method == "runtime/load":
        app_id = params.get("appId")
        if app_id not in APPS_INDEX or app_id == "loader-preview":
            raise LookupError("Unknown app")
        app = APPS_INDEX[app_id]
        return {
            "content": [{"type": "text", "text": f"已返回 {app.title} HTML。"}],
            "structuredContent": {
                "appId": app.slug,
                "title": app.title,
                "html": (APPS / app.filename).read_text(encoding="utf-8"),
                "connectDomains": app.connect_domains,
            },
        }
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
