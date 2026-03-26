"""Tests for the unified launcher."""

from __future__ import annotations

from launch import build_plan, parse_args


def test_default_plan_runs_both() -> None:
    args = parse_args([])
    plan = build_plan(args)
    assert plan.run_bot is True
    assert plan.run_web is True


def test_web_only_plan() -> None:
    args = parse_args(["--web-only"])
    plan = build_plan(args)
    assert plan.run_bot is False
    assert plan.run_web is True


def test_bot_only_plan() -> None:
    args = parse_args(["--bot-only"])
    plan = build_plan(args)
    assert plan.run_bot is True
    assert plan.run_web is False
