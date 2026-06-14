# Quark Transfer Tool

This tool accepts a Quark Drive share link, saves the shared content into your own Quark Drive, creates a new share link, and can optionally send the result to a cloud short-link tracker.

## Features

- Read Quark share links, passcodes, and cookies locally.
- Save shared resources into a target Quark Drive folder.
- Create a fresh Quark share link.
- Optionally create a cloud short link on `s.panlays.com`.
- Use the local tracker page to create temporary `127.0.0.1` tracking links.

## Always-On Local Service

QuarkTransfer starts automatically at Windows sign-in through the `QuarkTransferAlwaysOn` scheduled task and only listens on:

```text
http://127.0.0.1:8765
```

The watchdog restarts the server after an unexpected exit. The UI no longer contains a shutdown button, and the backend no longer exposes a shutdown endpoint.

To install or rebuild the task, run this command in PowerShell:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "\\wsl.localhost\Ubuntu-24.04\home\xuelong\projects\Tools\QuarkTransfer\install_always_on_task.ps1"
```

Mutating APIs use an automatically generated local token. It is stored in `config/local_token.txt`, loaded by the page automatically, and ignored by Git.

Tracker page:

```text
http://127.0.0.1:8765/tracker
```

## CSV Batch Transfer

Switch the page to "CSV Batch" and upload a CSV file to process transfers, new shares, short links, and Feishu synchronization sequentially.

Recommended headers:

```csv
文件名称,夸克链接,提取码
Example resource,https://pan.quark.cn/s/xxxx,abcd
```

- Title aliases: `资源名称`, `标题`, `软件关键词`, or `title`.
- URL aliases: `夸克网盘`, `链接`, `分享链接`, or `URL`.
- Passcode aliases: `密码`, `访问码`, `passcode`, or `pwd`.
- UTF-8 and GBK files are supported, with up to 100 valid rows per batch.
- Rows run in CSV order. One failed row does not stop the remaining rows.

## Fixed Target Folder

If you always save files into the same Quark folder, create:

```text
config/target_fid.txt
```

Put only the target folder fid in that file. The page will fill it into the target folder field on startup. Values entered on the page take priority.

## Cookie

After logging in to `https://pan.quark.cn`, open browser developer tools, refresh the page, and copy the full `Cookie` value from a `drive-pc.quark.cn` or `drive-h.quark.cn` request header.

You can paste the cookie into the page temporarily or store it locally:

```text
config/cookie.txt
```

You can also use an environment variable:

```powershell
$env:QUARK_COOKIE="paste the full Cookie here"
```

## Cloud Short-Link Tracker

The Cloudflare Worker lives in the `cloudflare-tracker` submodule. Production admin page:

```text
https://s.panlays.com/admin
```

Short-link format:

```text
https://s.panlays.com/abc123
```

## Security Notes

- Do not commit cookies, short-link tokens, logs, pid files, or machine-specific configuration.
- The `config/` directory keeps only `.gitkeep` by default.
- A cookie is a login credential. Do not share it with others.
- Only transfer and share content you have the right to process.
