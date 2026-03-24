"""Inline-keyboard and reply-keyboard builders for the Telegram bot."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from bot.i18n import t
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

# Format keys (used as callback data values)
FORMAT_KEYS = ("wireguard", "amnezia", "clash", "wiresock")


def _btn_generate() -> str:
    return t("btn_generate")


def _btn_status() -> str:
    return t("btn_status")


def _btn_help() -> str:
    return t("btn_help")


# Expose button labels as functions so handler filters can match them.
BTN_GENERATE = property(lambda self: t("btn_generate"))  # not used directly
BTN_STATUS = property(lambda self: t("btn_status"))
BTN_HELP = property(lambda self: t("btn_help"))


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Persistent reply-keyboard shown below the chat input."""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(t("btn_generate"))],
            [KeyboardButton(t("btn_status")), KeyboardButton(t("btn_help"))],
        ],
        resize_keyboard=True,
    )


def format_keyboard() -> InlineKeyboardMarkup:
    """Keyboard with VPN-config format options."""
    buttons = []
    for key in FORMAT_KEYS:
        label = t(f"fmt_{key}")
        desc = t(f"fmt_{key}_desc")
        buttons.append(
            [InlineKeyboardButton(f"{label} — {desc}", callback_data=f"{FORMAT_CB}{key}")]
        )
    return InlineKeyboardMarkup(buttons)


def dns_keyboard(configs: BotConfigs) -> InlineKeyboardMarkup:
    """Keyboard listing available DNS servers."""
    buttons = [
        [
            InlineKeyboardButton(
                f"🌐 {dns.name} ({', '.join(dns.servers)})",
                callback_data=f"{DNS_CB}{i}",
            )
        ]
        for i, dns in enumerate(configs.dns_servers)
    ]
    return InlineKeyboardMarkup(buttons)


def relay_keyboard(configs: BotConfigs) -> InlineKeyboardMarkup:
    """Keyboard listing available relay endpoints in a two-column grid."""
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for i, relay in enumerate(configs.relay_servers):
        row.append(
            InlineKeyboardButton(
                f"📡 {relay.name}",
                callback_data=f"{RELAY_CB}{i}",
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def routing_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for choosing full or split tunnel."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t("route_full"),
                    callback_data=f"{ROUTE_CB}full",
                )
            ],
            [
                InlineKeyboardButton(
                    t("route_split"),
                    callback_data=f"{ROUTE_CB}split",
                )
            ],
        ]
    )


def services_keyboard(
    configs: BotConfigs, selected: set[int]
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
                    f"{check} {svc.name}",
                    callback_data=f"{SVC_CB}{i}",
                )
            ]
        )
    buttons.append(
        [InlineKeyboardButton(t("btn_done"), callback_data=SVC_DONE_CB)]
    )
    return InlineKeyboardMarkup(buttons)


def confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirmation keyboard before generating the config."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(t("btn_confirm"), callback_data=CONFIRM_CB)],
            [InlineKeyboardButton(t("btn_back"), callback_data=f"{BACK_CB}start")],
        ]
    )
