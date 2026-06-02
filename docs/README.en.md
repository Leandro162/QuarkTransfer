# Quark Transfer Tool

This tool accepts a Quark Drive share link, saves the shared content into your own Quark Drive, creates a new share link, and can optionally send the result to a cloud short-link tracker.

## Features

- Read Quark share links, passcodes, and cookies locally.
- Save shared resources into a target Quark Drive folder.
- Create a fresh Quark share link.
- Optionally create a cloud short link on `s.panlays.com`.
- Use the local tracker page to create temporary `127.0.0.1` tracking links.

## Start the Local Tool

```bash
cd /home/xuelong/projects/Tools/QuarkTransfer
python3 server.py --port 8765
```

Then open:

```text
http://127.0.0.1:8765
```

Tracker page:

```text
http://127.0.0.1:8765/tracker
```

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
