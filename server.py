#!/usr/bin/env python3
from __future__ import annotations

import json
import mimetypes
import argparse
import os
import re
import uuid
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock, Thread
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from quark_transfer import QuarkClient, QuarkError, load_cookie, parse_share_url


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
TARGET_FID_FILE = ROOT / "config" / "target_fid.txt"
TRACKER_FILE = ROOT / "config" / "tracked_links.json"
SHORTLINK_TOKEN_FILE = ROOT / "config" / "shortlink_token.txt"
SHORTLINK_API_FILE = ROOT / "config" / "shortlink_api.txt"
FEISHU_CONFIG_FILE = ROOT / "config" / "feishu.json"
DEFAULT_SHORTLINK_API = "https://s.panlays.com/api/links"
FEISHU_TOKEN_API = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
FEISHU_RECORD_API = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
QUARK_SHARE_URL_RE = re.compile(r"https?://pan\.quark\.cn/s/[A-Za-z0-9_-]+(?:[/?#][^\s\"'<>，。；、]*)?", re.I)
PASSCODE_RE = re.compile(r"(?:提取码|提取碼|密码|密碼|访问码|口令|pwd|passcode|code)\s*[:：]?\s*([A-Za-z0-9]{4,12})", re.I)
DATE_YEAR = r"(?:19|20)\d{2}"
DATE_MONTH = r"(?:0?[1-9]|1[0-2])"
DATE_DAY = r"(?:0?[1-9]|[12]\d|3[01])"
CHINESE_DATE_TOKEN = rf"(?:{DATE_YEAR}\s*年\s*{DATE_MONTH}\s*月\s*{DATE_DAY}\s*日|{DATE_MONTH}\s*月\s*{DATE_DAY}\s*日)"
STRUCTURED_DATE_TOKEN = rf"(?:{DATE_YEAR}[./-]{DATE_MONTH}[./-]{DATE_DAY}|{DATE_MONTH}[./-]{DATE_DAY})"
COMPACT_DATE_TOKEN = r"(?:(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])|(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]))"
TITLE_DATE_TOKEN = rf"(?:{CHINESE_DATE_TOKEN}|{STRUCTURED_DATE_TOKEN})"
BRACKETED_DATE_RE = re.compile(rf"[\[【(（]\s*(?:{TITLE_DATE_TOKEN}|{COMPACT_DATE_TOKEN})\s*[\]】)）]")
TITLE_DATE_PREFIX_RE = re.compile(rf"^\s*{TITLE_DATE_TOKEN}(?:\s*[-_—–|·,，.。]+\s*|\s+)+")
TITLE_DATE_SUFFIX_RE = re.compile(rf"(?:\s*[-_—–|·,，.。]+\s*|\s+)+{TITLE_DATE_TOKEN}\s*$")
COMPACT_DATE_PREFIX_RE = re.compile(rf"^\s*{COMPACT_DATE_TOKEN}\s+")
COMPACT_DATE_SUFFIX_RE = re.compile(rf"\s+{COMPACT_DATE_TOKEN}\s*$")
CHINESE_DATE_PREFIX_RE = re.compile(rf"^\s*{CHINESE_DATE_TOKEN}\s*")
CHINESE_DATE_SUFFIX_RE = re.compile(rf"\s*{CHINESE_DATE_TOKEN}\s*$")
TRACKER_LOCK = Lock()


class AppHandler(BaseHTTPRequestHandler):
    server_version = "QuarkTransfer/1.0"

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            self.send_file(WEB_ROOT / "index.html")
            return
        if path == "/tracker":
            self.send_file(WEB_ROOT / "tracker.html")
            return
        if path == "/api/config":
            self.send_json(
                {
                    "ok": True,
                    "target_fid": load_target_fid(),
                    "shortlink_enabled": bool(load_shortlink_token()),
                    "shortlink_api": load_shortlink_api(),
                    "feishu_enabled": bool(load_feishu_config()),
                }
            )
            return
        if path == "/api/tracker/links":
            self.send_json({"ok": True, **tracker_snapshot(self.base_url())})
            return
        if path.startswith("/t/"):
            self.redirect_tracked_link(path.removeprefix("/t/"))
            return
        if path.startswith("/assets/"):
            self.send_file(WEB_ROOT / path.lstrip("/"))
            return
        self.send_json({"ok": False, "error": "Not found"}, status=404)

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/api/shutdown":
            self.send_json({"ok": True, "message": "本地服务正在关闭。"})
            Thread(target=self.server.shutdown, daemon=True).start()
            return

        if path == "/api/tracker/links":
            try:
                payload = self.read_json()
                link = create_tracked_link(payload, self.base_url())
                self.send_json({"ok": True, "link": link, **tracker_snapshot(self.base_url())})
            except ValueError as exc:
                self.send_json({"ok": False, "error": str(exc)}, status=400)
            except Exception as exc:  # noqa: BLE001
                self.send_json({"ok": False, "error": f"服务端错误: {exc}"}, status=500)
            return

        if path != "/api/transfer":
            self.send_json({"ok": False, "error": "Not found"}, status=404)
            return

        try:
            payload = self.read_json()
            result = transfer(payload)
            self.send_json(result)
        except QuarkError as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=400)
        except Exception as exc:  # noqa: BLE001
            self.send_json({"ok": False, "error": f"服务端错误: {exc}"}, status=500)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        if not raw:
            return {}
        return json.loads(raw)

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, file_path: Path) -> None:
        if not file_path.is_file():
            self.send_json({"ok": False, "error": "Not found"}, status=404)
            return
        body = file_path.read_bytes()
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        if file_path.suffix == ".html":
            content_type = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def redirect_tracked_link(self, link_id: str) -> None:
        target_url = record_visit(link_id)
        if not target_url:
            self.send_json({"ok": False, "error": "Tracked link not found"}, status=404)
            return
        self.send_response(302)
        self.send_header("Location", target_url)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def base_url(self) -> str:
        host = self.headers.get("Host") or "127.0.0.1:8765"
        return f"http://{host}"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(fmt % args)


def transfer(payload: dict[str, Any]) -> dict[str, Any]:
    raw_share = str(payload.get("url") or "").strip()
    if not raw_share:
        raise QuarkError("请输入夸克分享链接。")

    share_input = normalize_share_input(raw_share, str(payload.get("passcode") or ""))
    share = parse_share_url(share_input["url"], share_input["passcode"])
    cookie = load_cookie(str(payload.get("cookie") or ""))
    client = QuarkClient(cookie)

    stoken = client.get_stoken(share)
    detail = client.get_share_detail(share, stoken)
    files = detail["list"]
    manual_title = str(payload.get("share_title") or "").strip()
    detected_title = str(share_input.get("title") or detail.get("share", {}).get("title") or "").strip()
    cleaned_title = clean_detected_title(detected_title)
    title = manual_title or cleaned_title or detected_title or "Quark Share"

    target_fid = str(payload.get("target_fid") or "").strip() or load_target_fid() or "0"
    saved_fids = client.save_share(share, stoken, files, target_fid)
    share_info = client.create_share(saved_fids, title, expire_days=0, password="")

    result = {
        "ok": True,
        "title": title,
        "detected_title": detected_title,
        "title_cleaned": bool(not manual_title and detected_title and title != detected_title),
        "file_count": len(files),
        "saved_fids": saved_fids,
        "target_fid": target_fid,
        "share_url": share_info.get("share_url") or share_info.get("url") or "",
        "share_pwd": share_info.get("share_pwd") or share_info.get("password") or "",
        "share_url_with_pwd": share_info.get("share_url_with_pwd")
        or share_info.get("share_url")
        or share_info.get("url")
        or "",
    }
    if payload.get("auto_shortlink"):
        target_url = result["share_url_with_pwd"] or result["share_url"]
        try:
            shortlink = create_cloud_shortlink(
                {
                    "source_text": f"{title}\n{target_url}",
                    "title": title,
                    "url": target_url,
                    "passcode": result["share_pwd"],
                }
            )
            result["shortlink"] = shortlink
            result["short_url"] = shortlink.get("short_url") or ""
            try:
                result["feishu"] = sync_feishu_record(result)
            except Exception as exc:  # noqa: BLE001
                result["feishu_error"] = str(exc)
        except Exception as exc:  # noqa: BLE001
            result["shortlink_error"] = str(exc)
    return result


def normalize_share_input(raw: str, passcode: str) -> dict[str, str]:
    share_url = raw.strip()
    match = QUARK_SHARE_URL_RE.search(raw)
    if match:
        share_url = match.group(0)
    extracted_passcode = passcode.strip() or extract_passcode(raw)
    return {
        "url": share_url,
        "passcode": extracted_passcode,
        "title": extract_title(raw, share_url),
    }


def extract_passcode(raw: str) -> str:
    match = PASSCODE_RE.search(raw)
    return match.group(1) if match else ""


def extract_title(raw: str, share_url: str) -> str:
    text = raw.replace(share_url, "\n")
    for line in text.splitlines():
        cleaned = line.strip(" \t\r\n\"'「」[]【】")
        if not cleaned or "pan.quark.cn" in cleaned:
            continue
        quoted = re.search(r"分享了[「\"]([^」\"]+)[」\"]", cleaned)
        if quoted:
            return quoted.group(1).strip()
        cleaned = re.sub(r"^(资源名称|标题|名称)\s*[:：]\s*", "", cleaned).strip()
        if not cleaned or PASSCODE_RE.search(cleaned):
            continue
        if any(word in cleaned for word in ("复制", "打开", "链接", "提取码", "密码")) and len(cleaned) > 40:
            continue
        return cleaned[:80]
    return ""


def clean_detected_title(title: str) -> str:
    original = title.strip()
    if not original:
        return ""

    cleaned = original
    for _ in range(4):
        before = cleaned
        cleaned = BRACKETED_DATE_RE.sub(" ", cleaned)
        cleaned = CHINESE_DATE_PREFIX_RE.sub("", cleaned)
        cleaned = CHINESE_DATE_SUFFIX_RE.sub("", cleaned)
        cleaned = TITLE_DATE_PREFIX_RE.sub("", cleaned)
        cleaned = TITLE_DATE_SUFFIX_RE.sub("", cleaned)
        cleaned = COMPACT_DATE_PREFIX_RE.sub("", cleaned)
        cleaned = COMPACT_DATE_SUFFIX_RE.sub("", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = cleaned.strip(" \t\r\n-_—–|·,，.。[]【】()（）")
        if cleaned == before:
            break

    return cleaned or original


def load_target_fid() -> str:
    if TARGET_FID_FILE.exists():
        return TARGET_FID_FILE.read_text(encoding="utf-8").strip()
    return ""


def load_shortlink_api() -> str:
    value = os.environ.get("SHORTLINK_API", "").strip()
    if value:
        return value
    if SHORTLINK_API_FILE.exists():
        value = SHORTLINK_API_FILE.read_text(encoding="utf-8").strip()
        if value:
            return value
    return DEFAULT_SHORTLINK_API


def load_shortlink_token() -> str:
    value = os.environ.get("SHORTLINK_TOKEN", "").strip()
    if value:
        return value
    if SHORTLINK_TOKEN_FILE.exists():
        return SHORTLINK_TOKEN_FILE.read_text(encoding="utf-8").strip()
    return ""


def load_feishu_config() -> dict[str, str]:
    if not FEISHU_CONFIG_FILE.exists():
        return {}
    try:
        raw = json.loads(FEISHU_CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {
        "app_id": str(raw.get("app_id") or "").strip(),
        "app_secret": str(raw.get("app_secret") or "").strip(),
        "app_token": str(raw.get("app_token") or "").strip(),
        "table_id": str(raw.get("table_id") or "").strip(),
    }


def create_cloud_shortlink(payload: dict[str, Any]) -> dict[str, Any]:
    token = load_shortlink_token()
    if not token:
        raise RuntimeError("未配置短链管理 Token，请设置 config/shortlink_token.txt 或 SHORTLINK_TOKEN。")
    api_url = load_shortlink_api()
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        api_url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "QuarkTransfer/1.0",
        },
    )
    data = open_json(request, timeout=20)
    if not data.get("ok"):
        raise RuntimeError(str(data.get("error") or "短链生成失败"))
    link = data.get("link")
    if not isinstance(link, dict) or not link.get("short_url"):
        raise RuntimeError("短链服务没有返回 short_url")
    return link


def sync_feishu_record(result: dict[str, Any]) -> dict[str, Any]:
    config = load_feishu_config()
    if not all(config.values()):
        raise RuntimeError("未配置飞书同步，请设置 config/feishu.json。")

    tenant_token = get_feishu_tenant_token(config)
    api_url = FEISHU_RECORD_API.format(app_token=config["app_token"], table_id=config["table_id"])
    quark_url = result.get("share_url_with_pwd") or result.get("share_url") or ""
    short_url = result.get("short_url") or ""
    fields = {
        "文件名称": result.get("title") or "未命名资源",
        "软件关键词": result.get("title") or "未命名资源",
        "夸克网盘": {"text": quark_url, "link": quark_url},
        "短链": {"text": short_url, "link": short_url},
    }
    body = json.dumps({"fields": fields}, ensure_ascii=False).encode("utf-8")
    request = Request(
        api_url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {tenant_token}",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "QuarkTransfer/1.0",
        },
    )
    data = open_json(request, timeout=20)
    if data.get("code") != 0:
        raise RuntimeError(str(data.get("msg") or data.get("message") or "飞书同步失败"))
    return {
        "ok": True,
        "record_id": ((data.get("data") or {}).get("record") or {}).get("record_id") or "",
    }


def get_feishu_tenant_token(config: dict[str, str]) -> str:
    body = json.dumps(
        {
            "app_id": config["app_id"],
            "app_secret": config["app_secret"],
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(
        FEISHU_TOKEN_API,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "QuarkTransfer/1.0",
        },
    )
    data = open_json(request, timeout=20)
    if data.get("code") != 0 or not data.get("tenant_access_token"):
        raise RuntimeError(str(data.get("msg") or data.get("message") or "获取飞书访问凭证失败"))
    return str(data["tenant_access_token"])


def open_json(request: Request, timeout: int) -> dict[str, Any]:
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raw = exc.read().decode("utf-8")
    return json.loads(raw)


def tracker_snapshot(base_url: str) -> dict[str, Any]:
    with TRACKER_LOCK:
        data = load_tracker_data()
    today_key = today()
    links = [public_link(link, base_url, today_key) for link in data.get("links", [])]
    links.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return {
        "stats": {
            "today": sum(int(link.get("today_count", 0)) for link in links),
            "total": sum(int(link.get("total_count", 0)) for link in links),
            "links": len(links),
        },
        "links": links,
    }


def create_tracked_link(payload: dict[str, Any], base_url: str) -> dict[str, Any]:
    title = str(payload.get("title") or "").strip()
    url = str(payload.get("url") or "").strip()
    validate_track_url(url)
    with TRACKER_LOCK:
        data = load_tracker_data()
        link_id = unique_link_id(data)
        link = {
            "id": link_id,
            "title": title or "未命名资源",
            "url": url,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "total_count": 0,
            "daily_counts": {},
        }
        data.setdefault("links", []).append(link)
        save_tracker_data(data)
    return public_link(link, base_url, today())


def record_visit(link_id: str) -> str:
    link_id = link_id.strip().split("/", 1)[0]
    if not link_id:
        return ""
    with TRACKER_LOCK:
        data = load_tracker_data()
        for link in data.get("links", []):
            if link.get("id") != link_id:
                continue
            day = today()
            daily_counts = link.setdefault("daily_counts", {})
            daily_counts[day] = int(daily_counts.get(day, 0)) + 1
            link["total_count"] = int(link.get("total_count", 0)) + 1
            save_tracker_data(data)
            return str(link.get("url") or "")
    return ""


def load_tracker_data() -> dict[str, Any]:
    if not TRACKER_FILE.exists():
        return {"links": []}
    try:
        data = json.loads(TRACKER_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"links": []}
    if not isinstance(data, dict):
        return {"links": []}
    links = data.get("links")
    if not isinstance(links, list):
        data["links"] = []
    return data


def save_tracker_data(data: dict[str, Any]) -> None:
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def public_link(link: dict[str, Any], base_url: str, today_key: str) -> dict[str, Any]:
    daily_counts = link.get("daily_counts") if isinstance(link.get("daily_counts"), dict) else {}
    link_id = str(link.get("id") or "")
    return {
        "id": link_id,
        "title": str(link.get("title") or "未命名资源"),
        "url": str(link.get("url") or ""),
        "created_at": str(link.get("created_at") or ""),
        "today_count": int(daily_counts.get(today_key, 0)),
        "total_count": int(link.get("total_count", 0)),
        "track_url": f"{base_url}/t/{link_id}",
    }


def unique_link_id(data: dict[str, Any]) -> str:
    existing = {str(link.get("id")) for link in data.get("links", [])}
    while True:
        link_id = uuid.uuid4().hex[:8]
        if link_id not in existing:
            return link_id


def validate_track_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("请输入完整的 http/https 链接。")


def today() -> str:
    return date.today().isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Quark transfer and share tracker")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()
    address = (args.host, args.port)
    httpd = ThreadingHTTPServer(address, AppHandler)
    print(f"Quark Transfer HTML is running at http://{address[0]}:{address[1]}")
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
