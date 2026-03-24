"""Inline-keyboard and reply-keyboard builders for the Telegram bot."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from bot.i18n import t_user, available_languages
from core.config import BotConfigs

# Callback-data prefixes
FORMAT_CB = "fmt:"
DNS_CB = "dns:"
RELAY_CB = "relay:"
ROUTE_CB = "route:"
SVC_CB = "svc:"
SVC_DONE_CB = "svc:done"
CONFIRM_CB = "confirm"
BACK_CB = "back:"
LANG_CB = "lang:"
GENERATE_ANOTHER_CB = "gen_another"

# Format keys (used as callback data values)
FORMAT_KEYS = ("wireguard", "amnezia", "clash", "wiresock")


def main_menu_keyboard(user_data: dict | None = None) -> ReplyKeyboardMarkup:
    """Persistent reply-keyboard shown below the chat input."""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(t_user("btn_generate", user_data))],
            [KeyboardButton(t_user("btn_status", user_data)), KeyboardButton(t_user("btn_help", user_data))],
        ],
        resize_keyboard=True,
    )


def format_keyboard(user_data: dict | None = None) -> InlineKeyboardMarkup:
    """Keyboard with VPN-config format options."""
    buttons = []
    for key in FORMAT_KEYS:
        label = t_user(f"fmt_{key}", user_data)
        desc = t_user(f"fmt_{key}_desc", user_data)
        buttons.append(
            [InlineKeyboardButton(f"{label} — {desc}", callback_data=f"{FORMAT_CB}{key}")]
        )
    return InlineKeyboardMarkup(buttons)


def dns_keyboard(configs: BotConfigs, user_data: dict | None = None) -> InlineKeyboardMarkup:
    """Keyboard listing available DNS servers."""
    buttons = [
        [
            InlineKeyboardButton(
                f"🌐 {t_user('dns_' + dns.id, user_data)} ({', '.join(dns.servers)})",
                callback_data=f"{DNS_CB}{i}",
            )
        ]
        for i, dns in enumerate(configs.dns_servers)
    ]
    return InlineKeyboardMarkup(buttons)


def relay_keyboard(configs: BotConfigs, user_data: dict | None = None) -> InlineKeyboardMarkup:
    """Keyboard listing available relay endpoints in a two-column grid."""
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for i, relay in enumerate(configs.relay_servers):
        row.append(
            InlineKeyboardButton(
                f"📡 {t_user('relay_' + relay.id, user_data)}",
                callback_data=f"{RELAY_CB}{i}",
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def routing_keyboard(user_data: dict | None = None) -> InlineKeyboardMarkup:
    """Keyboard for choosing full or split tunnel."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t_user("route_full", user_data),
                    callback_data=f"{ROUTE_CB}full",
                )
            ],
            [
                InlineKeyboardButton(
                    t_user("route_split", user_data),
                    callback_data=f"{ROUTE_CB}split",
                )
            ],
        ]
    )


def services_keyboard(
    configs: BotConfigs, selected: set[int], user_data: dict | None = None
) -> InlineKeyboardMarkup:
    """Keyboard for toggling individual services in split-tunnel mode."""
    buttons: list[list[InlineKeyboardButton]] = []
    for i, svc in enumerate(configs.routing_services):
        if i == 0:
            # Index 0 is "Full Tunnel" – skip it in the split-tunnel picker
            continue
        check = "✅" if i in selected else "⬜"
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{check} {t_user('svc_' + svc.id, user_data)}",
                    callback_data=f"{SVC_CB}{i}",
                )
            ]
        )
    buttons.append(
        [InlineKeyboardButton(t_user("btn_done", user_data), callback_data=SVC_DONE_CB)]
    )
    return InlineKeyboardMarkup(buttons)


def confirm_keyboard(user_data: dict | None = None) -> InlineKeyboardMarkup:
    """Confirmation keyboard before generating the config."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(t_user("btn_confirm", user_data), callback_data=CONFIRM_CB)],
            [InlineKeyboardButton(t_user("btn_back", user_data), callback_data=f"{BACK_CB}start")],
        ]
    )


def language_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for choosing the bot language."""
    lang_labels = {"en": "🇬🇧 English", "ru": "🇷🇺 Русский"}
    buttons = [
        [
            InlineKeyboardButton(
                lang_labels.get(lang, lang.upper()),
                callback_data=f"{LANG_CB}{lang}",
            )
        ]
        for lang in available_languages()
    ]
    return InlineKeyboardMarkup(buttons)


def generate_another_keyboard(user_data: dict | None = None) -> InlineKeyboardMarkup:
    """Keyboard shown after a config is generated, offering to create another."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(t_user("btn_generate_another", user_data), callback_data=GENERATE_ANOTHER_CB)],
        ]
    )
