# 夸克网盘转存分享工具

这个工具可以输入夸克网盘分享链接，把内容转存到你自己的夸克网盘，再创建新的分享链接，并可选择发送到云端短链追踪服务。

## 功能

- 本地读取夸克分享链接、提取码和 Cookie。
- 转存资源到指定夸克网盘目录。
- 创建新的夸克分享链接。
- 可自动生成 `s.panlays.com` 云端短链。
- 本地追踪页面可生成 `127.0.0.1` 临时追踪链接。

## 启动本地工具

```bash
cd /home/xuelong/projects/Tools/QuarkTransfer
python3 server.py --port 8765
```

然后打开：

```text
http://127.0.0.1:8765
```

追踪页面：

```text
http://127.0.0.1:8765/tracker
```

## 固定保存目录

如果每次都保存到同一个夸克文件夹，可以创建：

```text
config/target_fid.txt
```

文件里只写一行目标文件夹 fid。页面打开时会自动把这个值填到“保存目录 fid”。页面里填写的值优先级更高。

## Cookie

登录 `https://pan.quark.cn` 后，打开浏览器开发者工具，刷新页面，在任意 `drive-pc.quark.cn` 或 `drive-h.quark.cn` 请求的 Request Headers 里复制完整 `Cookie` 值。

Cookie 可以临时粘贴到页面，也可以放到本地文件：

```text
config/cookie.txt
```

也可以用环境变量：

```powershell
$env:QUARK_COOKIE="这里粘贴完整 Cookie"
```

## 云端短链追踪

云端 Worker 位于 `cloudflare-tracker` 子模块，线上后台：

```text
https://s.panlays.com/admin
```

短链格式：

```text
https://s.panlays.com/abc123
```

## 安全注意

- 不要提交 Cookie、短链 Token、日志、pid 文件或本机配置。
- `config/` 目录默认只保留 `.gitkeep`。
- Cookie 相当于登录凭证，不要发给别人。
- 只转存和分享你有权处理的内容。
