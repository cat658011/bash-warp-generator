"""Inline-keyboard builders for the Telegram bot."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import BotConfigs

# Callback-data prefixes
FORMAT_CB = "fmt:"
DNS_CB = "dns:"
RELAY_CB = "relay:"
ROUTE_CB = "route:"
SVC_CB = "svc:"
SVC_DONE_CB = "svc:done"

_FORMAT_LABELS: dict[str, str] = {
    "wireguard": "\U0001f512 WireGuard",
    "amnezia": "\U0001f6e1 AmneziaWG",
    "clash": "\u2694\ufe0f Clash",
    "wiresock": "\U0001fa9f WireSock",
}


def format_keyboard() -> InlineKeyboardMarkup:
    """Keyboard with VPN-config format options."""
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"{FORMAT_CB}{key}")]
        for key, label in _FORMAT_LABELS.items()
    ]
    return InlineKeyboardMarkup(buttons)


def dns_keyboard(configs: BotConfigs) -> InlineKeyboardMarkup:
    """Keyboard listing available DNS servers."""
    buttons = [
        [
            InlineKeyboardButton(
                f"\U0001f310 {dns.name} ({', '.join(dns.servers)})",
                callback_data=f"{DNS_CB}{i}",
            )
        ]
        for i, dns in enumerate(configs.dns_servers)
    ]
    return InlineKeyboardMarkup(buttons)


def relay_keyboard(configs: BotConfigs) -> InlineKeyboardMarkup:
    """Keyboard listing available relay endpoints."""
    buttons = [
        [
            InlineKeyboardButton(
                f"\U0001f4e1 {relay.name}",
                callback_data=f"{RELAY_CB}{i}",
            )
        ]
        for i, relay in enumerate(configs.relay_servers)
    ]
    return InlineKeyboardMarkup(buttons)


def routing_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for choosing full or split tunnel."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "\U0001f30d Full Tunnel (All Traffic)",
                    callback_data=f"{ROUTE_CB}full",
                )
            ],
            [
                InlineKeyboardButton(
                    "\U0001f500 Split Tunnel (Select Services)",
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
        check = "\u2705" if i in selected else "\u2b1c"
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{check} {svc.name}",
                    callback_data=f"{SVC_CB}{i}",
                )
            ]
        )
    buttons.append(
        [InlineKeyboardButton("\u2714\ufe0f Done", callback_data=SVC_DONE_CB)]
    )
    return InlineKeyboardMarkup(buttons)
