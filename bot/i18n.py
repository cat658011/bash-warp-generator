"""Internationalisation helper for the Telegram bot.

Language files live in ``configs/i18n/<code>.json`` (e.g. ``en.json``,
``ru.json``).  The active language is chosen via the ``BOT_LANG``
environment variable (default: ``en``).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_LANG_DIR = Path(__file__).resolve().parent.parent / "configs" / "i18n"
_strings: dict[str, str] = {}
_current_lang: str = "en"


def load_language(lang: str | None = None) -> None:
    """Load a language file into the global string table.

    Parameters
    ----------
    lang:
        Language code (e.g. ``"en"``, ``"ru"``).  When *None*, the
        ``BOT_LANG`` environment variable is used, falling back to ``"en"``.
    """
    global _strings, _current_lang

    if lang is None:
        lang = os.environ.get("BOT_LANG", "en")

    path = _LANG_DIR / f"{lang}.json"
    if not path.exists():
        # Fall back to English when the requested file is missing.
        path = _LANG_DIR / "en.json"
        lang = "en"

    with open(path, encoding="utf-8") as fh:
        _strings = json.load(fh)
    _current_lang = lang


def t(key: str, **kwargs: Any) -> str:
    """Return a translated string for *key*.

    Keyword arguments are forwarded to :meth:`str.format` so the caller
    can fill in placeholders (e.g. ``t("config_generated", format="WG")``).

    If the key is missing the raw key name is returned to avoid crashes.
    """
    if not _strings:
        load_language()
    value = _strings.get(key, key)
    if kwargs:
        value = value.format(**kwargs)
    return value


def current_language() -> str:
    """Return the language code currently loaded."""
    return _current_lang


def available_languages() -> list[str]:
    """Return a sorted list of available language codes."""
    return sorted(p.stem for p in _LANG_DIR.glob("*.json"))
