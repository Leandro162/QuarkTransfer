# CSV Batch Transfer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reliable CSV batch transfer with short-link generation and Feishu synchronization.

**Architecture:** Parse CSV into normalized transfer payloads on the server, then sequentially reuse the existing `transfer()` workflow. Add a two-mode frontend that reads UTF-8/GBK files and renders per-row results.

**Tech Stack:** Python standard library, `unittest`, HTML, CSS, browser JavaScript.

---

### Task 1: Batch parser and runner

**Files:**
- Modify: `server.py`
- Create: `tests/test_batch_transfer.py`

- [ ] Write tests for aliases, invalid input, limits, ordering, and row-level failures.
- [ ] Run `python3 -m unittest tests.test_batch_transfer -v` and verify the tests fail because the batch functions do not exist.
- [ ] Implement `parse_csv_rows()` and `transfer_batch()`.
- [ ] Add `/api/transfer/batch` routing with normal JSON error handling.
- [ ] Run the tests and verify they pass.

### Task 2: Batch upload interface

**Files:**
- Modify: `web/index.html`

- [ ] Add single/CSV segmented mode controls.
- [ ] Add CSV picker, format guidance, and template download.
- [ ] Decode UTF-8 or GBK CSV content in the browser.
- [ ] Submit batch JSON and show summary plus per-row results.
- [ ] Preserve the existing single-transfer behavior.

### Task 3: Documentation and verification

**Files:**
- Modify: `docs/README.zh-CN.md`
- Modify: `docs/README.en.md`

- [ ] Document CSV columns, aliases, limits, and failure behavior.
- [ ] Run unit tests and Python compilation.
- [ ] Restart port 8765 from the Home repository and verify `/api/config` and the batch validation endpoint.
- [ ] Commit, push by SSH, fetch, and confirm `main` matches `origin/main`.
