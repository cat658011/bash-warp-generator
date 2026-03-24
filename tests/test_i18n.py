"""Tests for the bot i18n module."""

from __future__ import annotations

from bot.i18n import available_languages, current_language, load_language, t


def test_load_english() -> None:
    load_language("en")
    assert current_language() == "en"


def test_load_russian() -> None:
    load_language("ru")
    assert current_language() == "ru"
    # Reset to en so other tests are not affected
    load_language("en")


def test_fallback_to_english() -> None:
    load_language("nonexistent")
    assert current_language() == "en"


def test_translate_returns_string() -> None:
    load_language("en")
    assert isinstance(t("welcome"), str)
    assert len(t("welcome")) > 0


def test_translate_with_format_args() -> None:
    load_language("en")
    result = t("config_generated", format="WireGuard")
    assert "WireGuard" in result


def test_missing_key_returns_key() -> None:
    load_language("en")
    assert t("nonexistent_key_xyz") == "nonexistent_key_xyz"


def test_available_languages_includes_en_and_ru() -> None:
    langs = available_languages()
    assert "en" in langs
    assert "ru" in langs


def test_russian_btn_generate() -> None:
    load_language("ru")
    assert "Генерация" in t("btn_generate") or "конфиг" in t("btn_generate").lower()
    load_language("en")


def test_all_keys_present_in_both_languages() -> None:
    """Every key in en.json must also exist in ru.json and vice-versa."""
    import json
    from pathlib import Path

    lang_dir = Path(__file__).resolve().parent.parent / "bot" / "lang"
    with open(lang_dir / "en.json", encoding="utf-8") as f:
        en_keys = set(json.load(f).keys())
    with open(lang_dir / "ru.json", encoding="utf-8") as f:
        ru_keys = set(json.load(f).keys())

    assert en_keys == ru_keys, f"Missing in ru: {en_keys - ru_keys}, missing in en: {ru_keys - en_keys}"
