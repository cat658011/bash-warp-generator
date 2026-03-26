#!/usr/bin/env python3
"""Unified launcher for bot and web services."""

from __future__ import annotations

import argparse
import signal
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class LaunchPlan:
    run_bot: bool
    run_web: bool


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch bot and/or web service")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--web-only", action="store_true", help="Launch only web server")
    group.add_argument("--bot-only", action="store_true", help="Launch only telegram bot")
    return parser.parse_args(argv)


def build_plan(args: argparse.Namespace) -> LaunchPlan:
    if args.web_only:
        return LaunchPlan(run_bot=False, run_web=True)
    if args.bot_only:
        return LaunchPlan(run_bot=True, run_web=False)
    return LaunchPlan(run_bot=True, run_web=True)


def _terminate(proc: subprocess.Popen[bytes]) -> None:
    if proc.poll() is None:
        proc.terminate()


def _wait_all(processes: list[subprocess.Popen[bytes]]) -> None:
    for proc in processes:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    plan = build_plan(args)

    processes: list[subprocess.Popen[bytes]] = []
    if plan.run_bot:
        processes.append(subprocess.Popen(["python", "-m", "bot"]))
    if plan.run_web:
        processes.append(subprocess.Popen(["node", "web/server.js"]))

    if not processes:
        return 0

    def handle_signal(_signum: int, _frame: object) -> None:
        for proc in processes:
            _terminate(proc)
        _wait_all(processes)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    while True:
        for proc in processes:
            code = proc.poll()
            if code is not None:
                for other in processes:
                    if other is not proc:
                        _terminate(other)
                _wait_all(processes)
                return int(code)
        signal.pause()


if __name__ == "__main__":
    raise SystemExit(main())
