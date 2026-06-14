# 夸克网盘转存分享工具

这个工具可以输入夸克网盘分享链接，把内容转存到你自己的夸克网盘，再创建新的分享链接，并可选择发送到云端短链追踪服务。

## 功能

- 本地读取夸克分享链接、提取码和 Cookie。
- 转存资源到指定夸克网盘目录。
- 创建新的夸克分享链接。
- 可自动生成 `s.panlays.com` 云端短链。
- 本地追踪页面可生成 `127.0.0.1` 临时追踪链接。

## 常驻本地服务

QuarkTransfer 通过 Windows 登录计划任务 `QuarkTransferAlwaysOn` 自动启动，并只监听：

```text
http://127.0.0.1:8765
```

守护脚本会在服务异常退出后自动重启。页面不再提供关闭按钮，后端也不再暴露关闭接口。

首次安装或需要重建计划任务时，在 PowerShell 中运行：

```powershell
powershell.exe -ExecutionPolicy Bypass -File "\\wsl.localhost\Ubuntu-24.04\home\xuelong\projects\Tools\QuarkTransfer\install_always_on_task.ps1"
```

写接口使用自动生成的本机令牌保护。令牌保存在 `config/local_token.txt`，页面会自动读取，无需手工填写。该文件已被 Git 忽略。

追踪页面：

```text
http://127.0.0.1:8765/tracker
```

## CSV 批量转存

在页面切换到“CSV 批量”，上传 CSV 后即可按顺序逐条执行转存、创建新分享、生成短链和同步飞书。

推荐表头：

```csv
文件名称,夸克链接,提取码
示例资源,https://pan.quark.cn/s/xxxx,abcd
```

- “文件名称”也支持“资源名称”“标题”“软件关键词”或 `title`。
- “夸克链接”也支持“夸克网盘”“链接”“分享链接”或 `URL`。
- “提取码”也支持“密码”“访问码”“passcode”或 `pwd`。
- 支持 UTF-8 和 GBK 编码，单次最多处理 100 条有效数据。
- 按 CSV 行号顺序处理；某一行失败不会中断后续任务。

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
