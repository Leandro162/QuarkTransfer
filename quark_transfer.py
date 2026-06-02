#!/usr/bin/env python3
"""
Transfer a Quark share into your own Quark drive, then create a new share link.

This script uses Quark web endpoints with your own browser Cookie. It does not
ask for, store, or transmit your account password.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen


API_PARAMS = {"pr": "ucpro", "fr": "pc", "uc_param_str": ""}
COOKIE_FILE = Path("config/cookie.txt")


class QuarkError(RuntimeError):
    pass


@dataclass
class ShareInput:
    pwd_id: str
    passcode: str = ""
    pdir_fid: str = "0"


class QuarkClient:
    def __init__(self, cookie: str, timeout: int = 30) -> None:
        cookie = cookie.strip()
        if not cookie:
            raise QuarkError("Cookie 为空。请设置 QUARK_COOKIE 或写入 config/cookie.txt。")
        self.cookie = cookie
        self.timeout = timeout

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        referer: str = "https://pan.quark.cn/",
    ) -> dict[str, Any]:
        if params:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{urlencode(params)}"

        data = None
        headers = {
            "Cookie": self.cookie,
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": referer,
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://pan.quark.cn",
        }
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json;charset=UTF-8"

        req = Request(url, data=data, headers=headers, method=method.upper())
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                text = resp.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            raise QuarkError(f"HTTP {exc.code}: {text[:500]}") from exc
        except URLError as exc:
            raise QuarkError(f"网络请求失败: {exc.reason}") from exc

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise QuarkError(f"响应不是 JSON: {text[:500]}") from exc

        code = payload.get("code")
        status = payload.get("status")
        if code not in (None, 0) and status not in (200, "200"):
            message = payload.get("message") or payload.get("msg") or payload
            raise QuarkError(f"接口返回失败 code={code}: {message}")
        return payload

    def get_stoken(self, share: ShareInput) -> str:
        payload = self.request(
            "POST",
            "https://drive-h.quark.cn/1/clouddrive/share/sharepage/token",
            params=timed_params(),
            body={"pwd_id": share.pwd_id, "passcode": share.passcode},
            referer=f"https://pan.quark.cn/s/{share.pwd_id}",
        )
        stoken = payload.get("data", {}).get("stoken")
        if not stoken:
            raise QuarkError("没有拿到 stoken，可能是链接失效、提取码错误或 Cookie 失效。")
        return stoken

    def get_share_detail(self, share: ShareInput, stoken: str) -> dict[str, Any]:
        payload = self.request(
            "GET",
            "https://drive-h.quark.cn/1/clouddrive/share/sharepage/detail",
            params={
                **API_PARAMS,
                "pwd_id": share.pwd_id,
                "stoken": stoken,
                "pdir_fid": share.pdir_fid,
                "force": 0,
                "_page": 1,
                "_size": 1000,
                "_fetch_banner": 1,
                "_fetch_share": 1,
                "_fetch_total": 1,
                "_sort": "file_type:asc,updated_at:desc",
            },
            referer=f"https://pan.quark.cn/s/{share.pwd_id}",
        )
        data = payload.get("data") or {}
        if not data.get("list"):
            raise QuarkError("分享目录为空，或无法读取分享文件列表。")
        return data

    def save_share(
        self,
        share: ShareInput,
        stoken: str,
        files: list[dict[str, Any]],
        target_fid: str,
    ) -> list[str]:
        fid_list = [item["fid"] for item in files if item.get("fid")]
        token_list = [
            item.get("share_fid_token") or item.get("fid_token")
            for item in files
            if item.get("fid")
        ]
        if not fid_list or len(fid_list) != len(token_list) or any(not x for x in token_list):
            raise QuarkError("无法从分享详情提取 fid 或 share_fid_token。")

        payload = self.request(
            "POST",
            "https://drive-pc.quark.cn/1/clouddrive/share/sharepage/save",
            params=timed_params(),
            body={
                "fid_list": fid_list,
                "fid_token_list": token_list,
                "to_pdir_fid": target_fid,
                "pwd_id": share.pwd_id,
                "stoken": stoken,
                "pdir_fid": share.pdir_fid,
                "scene": "link",
            },
            referer=f"https://pan.quark.cn/s/{share.pwd_id}",
        )

        data = payload.get("data") or {}
        if data.get("save_as", {}).get("save_as_top_fids"):
            return data["save_as"]["save_as_top_fids"]
        task_id = data.get("task_id")
        if not task_id:
            raise QuarkError(f"转存接口没有返回 task_id: {payload}")
        task = self.poll_task(task_id, title="转存")
        fids = task.get("save_as", {}).get("save_as_top_fids") or []
        if not fids:
            raise QuarkError(f"转存完成但没有返回新文件 ID: {task}")
        return fids

    def create_share(
        self,
        fids: list[str],
        title: str,
        *,
        expire_days: int = 0,
        password: str = "",
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "fid_list": fids,
            "title": title[:80] or "Quark Share",
            "url_type": 1,
            "expired_type": 1,
            "expire_time": 0,
        }
        if expire_days > 0:
            body["expired_type"] = 2
            body["expire_time"] = expire_days * 86400
        if password:
            body["password"] = password

        payload = self.request(
            "POST",
            "https://drive-pc.quark.cn/1/clouddrive/share",
            params=timed_params(),
            body=body,
        )
        data = payload.get("data") or {}
        share_id = data.get("share_id")
        if not share_id and data.get("task_id"):
            task = self.poll_task(data["task_id"], title="创建分享")
            share_id = task.get("share_id")
        if not share_id:
            raise QuarkError(f"创建分享成功但没有拿到 share_id: {payload}")
        data = self.get_share_url(str(share_id))
        share_url = data.get("share_url") or data.get("url") or ""
        share_pwd = data.get("share_pwd") or data.get("password") or data.get("passcode") or ""
        if share_url and share_pwd:
            data["share_url_with_pwd"] = add_query_param(share_url, "pwd", share_pwd)
        return data

    def get_share_url(self, share_id: str) -> dict[str, Any]:
        payload = self.request(
            "POST",
            "https://drive-pc.quark.cn/1/clouddrive/share/password",
            params=timed_params(),
            body={"share_id": share_id},
        )
        data = payload.get("data") or {}
        share_url = data.get("share_url") or data.get("url")
        if not share_url:
            raise QuarkError(f"无法取得分享链接: {payload}")
        return data

    def poll_task(self, task_id: str, *, title: str, attempts: int = 40) -> dict[str, Any]:
        for index in range(attempts):
            payload = self.request(
                "GET",
                "https://drive-pc.quark.cn/1/clouddrive/task",
                params={**timed_params(), "task_id": task_id, "retry_index": index},
            )
            data = payload.get("data") or {}
            status = data.get("status")
            if status == 2:
                return data
            if status in (3, 4, -1):
                raise QuarkError(f"{title}任务失败: {data}")
            time.sleep(1.2)
        raise QuarkError(f"{title}任务超时: {task_id}")


def timed_params() -> dict[str, Any]:
    return {
        **API_PARAMS,
        "__dt": random.randint(100, 999),
        "__t": int(time.time() * 1000),
    }


def parse_share_url(raw: str, passcode: str = "") -> ShareInput:
    raw = raw.strip()
    parsed = urlparse(raw)
    query = parse_qs(parsed.query)
    pwd_id = ""

    match = re.search(r"/s/([A-Za-z0-9_-]+)", parsed.path)
    if match:
        pwd_id = match.group(1)
    elif re.fullmatch(r"[A-Za-z0-9_-]{6,32}", raw):
        pwd_id = raw

    if not pwd_id:
        raise QuarkError("无法从输入中识别夸克分享 ID，请传入 https://pan.quark.cn/s/... 链接。")

    extracted_passcode = first_query_value(query, "pwd", "password", "passcode", "code")
    pdir_fid = "0"
    hash_match = re.search(r"/share/([A-Za-z0-9_-]+)", parsed.fragment)
    if hash_match:
        pdir_fid = hash_match.group(1)

    return ShareInput(
        pwd_id=pwd_id,
        passcode=passcode or extracted_passcode or "",
        pdir_fid=pdir_fid,
    )


def first_query_value(query: dict[str, list[str]], *names: str) -> str:
    for name in names:
        values = query.get(name)
        if values:
            return values[0]
    return ""


def add_query_param(url: str, name: str, value: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    query[name] = [value]
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(query, doseq=True),
            parsed.fragment,
        )
    )


def load_cookie(cli_cookie: str = "") -> str:
    if cli_cookie:
        return cli_cookie
    if os.environ.get("QUARK_COOKIE"):
        return os.environ["QUARK_COOKIE"]
    if COOKIE_FILE.exists():
        return COOKIE_FILE.read_text(encoding="utf-8").strip()
    return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="把夸克分享链接转存到自己的网盘，并输出新的分享链接。"
    )
    parser.add_argument("url", help="夸克分享链接，例如 https://pan.quark.cn/s/xxxx")
    parser.add_argument("--cookie", help="夸克 Cookie。也可使用 QUARK_COOKIE 或 config/cookie.txt。")
    parser.add_argument("--passcode", default="", help="提取码。也可写在链接 ?pwd=1234。")
    parser.add_argument("--target-fid", default="0", help="保存到自己的目标目录 fid，默认 0 根目录。")
    parser.add_argument("--share-title", default="", help="新分享标题，默认沿用原分享标题。")
    parser.add_argument("--share-password", default="", help="给新分享设置提取码，默认不设置。")
    parser.add_argument("--expire-days", type=int, default=0, help="新分享有效天数，0 表示永久。")
    parser.add_argument("--no-share", action="store_true", help="只转存，不创建新分享链接。")
    parser.add_argument("--json", action="store_true", help="只输出 JSON，便于脚本调用。")
    args = parser.parse_args(argv)

    try:
        share = parse_share_url(args.url, args.passcode)
        client = QuarkClient(load_cookie(args.cookie or ""))

        log("获取分享 token...", quiet=args.json)
        stoken = client.get_stoken(share)

        log("读取分享文件列表...", quiet=args.json)
        detail = client.get_share_detail(share, stoken)
        files = detail["list"]
        title = args.share_title or detail.get("share", {}).get("title") or "Quark Share"

        log(f"开始转存 {len(files)} 个项目...", quiet=args.json)
        saved_fids = client.save_share(share, stoken, files, args.target_fid)

        result: dict[str, Any] = {
            "ok": True,
            "title": title,
            "saved_fids": saved_fids,
        }
        if not args.no_share:
            log("创建新的分享链接...", quiet=args.json)
            share_info = client.create_share(
                saved_fids,
                title,
                expire_days=args.expire_days,
                password=args.share_password,
            )
            result["share_url"] = share_info.get("share_url") or share_info.get("url")
            result["share_pwd"] = share_info.get("share_pwd") or share_info.get("password") or ""
            result["share_url_with_pwd"] = (
                share_info.get("share_url_with_pwd") or result["share_url"]
            )

        print(json.dumps(result, ensure_ascii=False, indent=None if args.json else 2))
        return 0
    except QuarkError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


def log(message: str, *, quiet: bool) -> None:
    if not quiet:
        print(message, file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
