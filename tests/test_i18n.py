"""Tests for the bot i18n module."""

from __future__ import annotations

from bot.i18n import available_languages, current_language, load_language, t, t_user


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

    lang_dir = Path(__file__).resolve().parent.parent / "configs" / "i18n"
    with open(lang_dir / "en.json", encoding="utf-8") as f:
        en_keys = set(json.load(f).keys())
    with open(lang_dir / "ru.json", encoding="utf-8") as f:
        ru_keys = set(json.load(f).keys())

    assert en_keys == ru_keys, f"Missing in ru: {en_keys - ru_keys}, missing in en: {ru_keys - en_keys}"


def test_config_ids_have_i18n_keys() -> None:
    """Every config id must have a corresponding i18n key."""
    import json
    from pathlib import Path

    configs_dir = Path(__file__).resolve().parent.parent / "configs"
    lang_dir = configs_dir / "i18n"

    with open(lang_dir / "en.json", encoding="utf-8") as f:
        en = json.load(f)

    with open(configs_dir / "dns_servers.json", encoding="utf-8") as f:
        for item in json.load(f):
            key = "dns_" + item["id"]
            assert key in en, f"Missing i18n key: {key}"

    with open(configs_dir / "relay_servers.json", encoding="utf-8") as f:
        for item in json.load(f):
            key = "relay_" + item["id"]
            assert key in en, f"Missing i18n key: {key}"

    with open(configs_dir / "routing_services.json", encoding="utf-8") as f:
        for item in json.load(f):
            key = "svc_" + item["id"]
            assert key in en, f"Missing i18n key: {key}"


def test_t_user_returns_user_language() -> None:
    """t_user() with user_data['lang'] returns the correct language."""
    load_language("en")  # Global is English

    # User prefers Russian → should get Russian text
    ru_result = t_user("btn_generate", {"lang": "ru"})
    assert "Генерация" in ru_result or "конфиг" in ru_result.lower()

    # User prefers English → should get English text
    en_result = t_user("btn_generate", {"lang": "en"})
    assert "Generate" in en_result

    # Verify they are different
    assert ru_result != en_result


def test_t_user_falls_back_to_global() -> None:
    """t_user() without user_data falls back to the global language."""
    load_language("en")
    result_none = t_user("btn_generate", None)
    result_empty = t_user("btn_generate", {})
    assert "Generate" in result_none
    assert "Generate" in result_empty


def test_t_user_with_format_args() -> None:
    """t_user() forwards format keyword arguments."""
    load_language("en")
    result = t_user("config_generated", {"lang": "ru"}, format="WireGuard")
    assert "WireGuard" in result


def test_help_text_is_user_facing() -> None:
    """Help text should contain user-facing guides, not developer instructions."""
    for lang in available_languages():
        load_language(lang)
        help_text = t("help")
        # Should NOT contain developer instructions
        assert "configs/dns_servers.json" not in help_text, f"[{lang}] help contains dev path"
        assert "configs/relay_servers.json" not in help_text, f"[{lang}] help contains dev path"
        assert "configs/routing_services.json" not in help_text, f"[{lang}] help contains dev path"
        assert "i18n file" not in help_text.lower(), f"[{lang}] help contains dev reference"
    load_language("en")
