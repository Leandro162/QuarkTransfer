# CSV Batch Transfer Design

## Goal

Add a CSV upload mode beside the existing single-share form. Each valid CSV row is processed in order through the existing Quark transfer, short-link creation, and Feishu synchronization workflow.

## Input

The preferred columns are:

```csv
文件名称,夸克链接,提取码
示例资源,https://pan.quark.cn/s/xxxx,abcd
```

Common aliases are accepted for title, URL, and passcode. Empty rows are ignored. A request may contain at most 100 valid rows.

## Processing

The browser reads UTF-8 or GBK CSV files and sends the text to `/api/transfer/batch`. The server parses the rows and calls the existing `transfer()` function sequentially. A failed row is recorded without stopping later rows.

## Output

The response contains total, succeeded, and failed counts plus one result per row. The page shows a compact list with the generated Quark link, short link, Feishu status, or error.

## Safety

Cookie, target folder, and short-link settings remain shared with the single mode. No credentials are written into CSV files or repository files.
