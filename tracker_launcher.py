#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
PID_FILE = ROOT / "config" / "tracker.pid"
LOG_FILE = ROOT / "config" / "tracker.log"
PYTHON = Path(sys.executable)
DEFAULT_PORT = 8765


def main() -> int:
    parser = argparse.ArgumentParser(description="Start or stop the Quark transfer tool in the background")
    parser.add_argument("action", choices=["start", "stop", "status"])
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    if args.action == "start":
        return start(args.port)
    if args.action == "stop":
        return stop(args.port)
    return status(args.port)


def start(port: int) -> int:
    if is_alive(port):
        write_line(f"Quark transfer is already running: http://127.0.0.1:{port}/")
        return 0

    ROOT.joinpath("config").mkdir(exist_ok=True)
    log = LOG_FILE.open("a", encoding="utf-8")
    process = subprocess.Popen(
        [str(PYTHON), str(ROOT / "server.py"), "--port", str(port)],
        cwd=str(ROOT),
        stdout=log,
        stderr=log,
        stdin=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
    )
    PID_FILE.write_text(str(process.pid), encoding="utf-8")

    for _ in range(30):
        if is_alive(port):
            write_line(f"Quark transfer started: http://127.0.0.1:{port}/")
            return 0
        time.sleep(0.2)

    write_line(f"Quark transfer did not respond. See log: {LOG_FILE}")
    return 1


def stop(port: int) -> int:
    pid = read_pid()
    if not pid:
        pid = pid_for_port(port)
    if not pid:
        write_line("Tracker is not running.")
        return 0

    result = subprocess.run(
        ["taskkill", "/PID", str(pid), "/F"],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
        check=False,
    )
    PID_FILE.unlink(missing_ok=True)
    if result.returncode == 0:
        write_line("Tracker stopped.")
        return 0
    write_line((result.stderr or result.stdout or "Quark transfer process was not running.").strip())
    return 0


def pid_for_port(port: int) -> int | None:
    result = subprocess.run(
        ["netstat", "-ano", "-p", "tcp"],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
        check=False,
    )
    if result.returncode != 0:
        return None
    marker = f":{port}"
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        local_address, state, pid = parts[1], parts[3], parts[4]
        if state.upper() == "LISTENING" and local_address.endswith(marker):
            try:
                return int(pid)
            except ValueError:
                return None
    return None


def status(port: int) -> int:
    if is_alive(port):
        write_line(f"Quark transfer is running: http://127.0.0.1:{port}/")
        return 0
    write_line("Quark transfer is not running.")
    return 1


def is_alive(port: int) -> bool:
    try:
        with urlopen(f"http://127.0.0.1:{port}/api/config", timeout=1.5) as response:
            return response.status == 200
    except URLError:
        return False
    except TimeoutError:
        return False


def read_pid() -> int | None:
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def write_line(text: str) -> None:
    print(text)


if __name__ == "__main__":
    raise SystemExit(main())
