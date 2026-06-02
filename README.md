# QuarkTransfer

本地夸克网盘转存工具 + 云端短链追踪服务入口。

Local Quark Drive transfer tool with a cloud short-link tracker entrypoint.

## Languages

- [中文文档](docs/README.zh-CN.md)
- [English README](docs/README.en.md)

## Project Metadata

- **Name:** QuarkTransfer
- **Type:** Local web tool + Cloudflare Worker short-link tracker
- **Local URL:** `http://127.0.0.1:8765`
- **Cloud admin:** `https://s.panlays.com/admin`
- **Cloud tracker module:** `cloudflare-tracker`
- **Tags:** `quark-drive`, `short-link`, `cloudflare-workers`, `d1`, `local-tool`, `tracker`
- **License:** Not specified

## Repository Layout

```text
.
├── docs/
│   ├── README.zh-CN.md
│   └── README.en.md
├── web/
│   ├── index.html
│   └── tracker.html
├── cloudflare-tracker/
├── server.py
├── quark_transfer.py
└── tracker_launcher.py
```

Clone with submodules when you need the Cloudflare Worker code:

```bash
git clone --recurse-submodules <repo-url>
```

## Security

Runtime secrets and machine-local files are intentionally ignored by Git, including cookies, short-link tokens, logs, pid files, caches, and generated binaries. Keep credentials in `config/` or environment variables, never in committed files.
