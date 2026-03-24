"""Telegram bot handlers — conversation flow for generating WARP configs."""

from __future__ import annotations

import logging
from io import BytesIO

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from core.config import BotConfigs
from core.generators import (
    GENERATORS,
    AmneziaWGGenerator,
    GeneratorParams,
)
from core.warp import register_warp

from bot.keyboards import (
    BTN_GENERATE,
    BTN_HELP,
    BTN_STATUS,
    DNS_CB,
    FORMAT_CB,
    RELAY_CB,
    ROUTE_CB,
    SVC_CB,
    SVC_DONE_CB,
    dns_keyboard,
    format_keyboard,
    main_menu_keyboard,
    relay_keyboard,
    routing_keyboard,
    services_keyboard,
)

logger = logging.getLogger(__name__)

# Conversation states
SELECT_FORMAT, SELECT_DNS, SELECT_RELAY, SELECT_ROUTING, SELECT_SERVICES = range(5)

_WELCOME_TEXT = (
    "\U0001f680 <b>WARP Config Generator</b>\n"
    "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
    "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
    "Generate <b>Cloudflare WARP</b> VPN configs\n"
    "in multiple formats with one tap.\n\n"
    "\U0001f4cb <b>Supported formats:</b>\n"
    "  \U0001f512 WireGuard\n"
    "  \U0001f6e1\ufe0f AmneziaWG\n"
    "  \u2694\ufe0f Clash / Clash Meta\n"
    "  \U0001fa9f WireSock (Windows)\n\n"
    "Use the menu below to get started \u2b07\ufe0f"
)

_HELP_TEXT = (
    "\u2753 <b>Help &amp; Guides</b>\n"
    "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
    "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
    "\U0001f4d6 <b>How to add a custom DNS server</b>\n"
    "Open <code>configs/dns_servers.json</code> and add:\n"
    "<pre>{\n"
    '  "name": "My DNS",\n'
    '  "servers": ["10.0.0.1", "10.0.0.2"]\n'
    "}</pre>\n\n"
    "\U0001f4d6 <b>How to add a relay endpoint</b>\n"
    "Open <code>configs/relay_servers.json</code> and add:\n"
    "<pre>{\n"
    '  "name": "Custom Relay",\n'
    '  "endpoint": "203.0.113.1:51820"\n'
    "}</pre>\n\n"
    "\U0001f4d6 <b>How to add a split-tunnel service</b>\n"
    "Open <code>configs/routing_services.json</code> and add:\n"
    "<pre>{\n"
    '  "name": "My Service",\n'
    '  "routes": ["203.0.113.0/24"]\n'
    "}</pre>\n\n"
    "\U0001f504 Restart the bot after editing config files.\n\n"
    "\U0001f6e0\ufe0f <b>Commands:</b>\n"
    "/start \u2014 show welcome &amp; menu\n"
    "/cancel \u2014 cancel current generation"
)


def _configs(context: ContextTypes.DEFAULT_TYPE) -> BotConfigs:
    return context.bot_data["configs"]


# ------------------------------------------------------------------
# /start  &  "🚀 Generate Config" button
# ------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message and show the persistent reply keyboard."""
    assert update.message is not None
    await update.message.reply_text(
        _WELCOME_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


async def generate_entry(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Show the format picker (entry-point for the conversation)."""
    assert update.message is not None
    await update.message.reply_text(
        "\U0001f4e6 <b>Step 1/4</b> \u2014 Choose output format:",
        parse_mode="HTML",
        reply_markup=format_keyboard(),
    )
    return SELECT_FORMAT


# ------------------------------------------------------------------
# 📊 WARP Status
# ------------------------------------------------------------------
async def warp_status(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Send a link to the WARP status Telegram channel."""
    assert update.message is not None
    await update.message.reply_text(
        "\U0001f4ca <b>WARP Status</b>\n\n"
        "Check the current Cloudflare WARP service status:\n"
        "\U0001f449 <a href=\"https://t.me/cfwarpstatus\">@cfwarpstatus</a>",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


# ------------------------------------------------------------------
# ❓ Help
# ------------------------------------------------------------------
async def help_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Display help text with configuration guides."""
    assert update.message is not None
    await update.message.reply_text(
        _HELP_TEXT,
        parse_mode="HTML",
    )


# ------------------------------------------------------------------
# Step 1 — format
# ------------------------------------------------------------------
async def on_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None and query.data is not None and context.user_data is not None
    await query.answer()

    context.user_data["format"] = query.data.removeprefix(FORMAT_CB)

    await query.edit_message_text(
        "\U0001f310 <b>Step 2/4</b> \u2014 Select a DNS server:",
        parse_mode="HTML",
        reply_markup=dns_keyboard(_configs(context)),
    )
    return SELECT_DNS


# ------------------------------------------------------------------
# Step 2 — DNS
# ------------------------------------------------------------------
async def on_dns(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None and query.data is not None and context.user_data is not None
    await query.answer()

    context.user_data["dns_idx"] = int(query.data.removeprefix(DNS_CB))

    await query.edit_message_text(
        "\U0001f4e1 <b>Step 3/4</b> \u2014 Select a relay server (endpoint):",
        parse_mode="HTML",
        reply_markup=relay_keyboard(_configs(context)),
    )
    return SELECT_RELAY


# ------------------------------------------------------------------
# Step 3 — relay
# ------------------------------------------------------------------
async def on_relay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None and query.data is not None and context.user_data is not None
    await query.answer()

    context.user_data["relay_idx"] = int(query.data.removeprefix(RELAY_CB))

    await query.edit_message_text(
        "\U0001f500 <b>Step 4/4</b> \u2014 Select routing mode:",
        parse_mode="HTML",
        reply_markup=routing_keyboard(),
    )
    return SELECT_ROUTING


# ------------------------------------------------------------------
# Step 4 — routing mode
# ------------------------------------------------------------------
async def on_routing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None and query.data is not None and context.user_data is not None
    await query.answer()

    mode = query.data.removeprefix(ROUTE_CB)

    if mode == "full":
        context.user_data["routing"] = "full"
        return await _generate(update, context)

    context.user_data["routing"] = "split"
    context.user_data["selected_svcs"] = set()

    await query.edit_message_text(
        "\U0001f500 Select services to route through WARP:\n"
        "(tap to toggle, then press <b>Done</b>)",
        parse_mode="HTML",
        reply_markup=services_keyboard(_configs(context), set()),
    )
    return SELECT_SERVICES


# ------------------------------------------------------------------
# Step 5 — service toggle
# ------------------------------------------------------------------
async def on_service_toggle(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    assert query is not None and query.data is not None and context.user_data is not None
    await query.answer()

    if query.data == SVC_DONE_CB:
        return await _generate(update, context)

    idx = int(query.data.removeprefix(SVC_CB))
    selected: set[int] = context.user_data.setdefault("selected_svcs", set())

    if idx in selected:
        selected.discard(idx)
    else:
        selected.add(idx)

    await query.edit_message_text(
        "\U0001f500 Select services to route through WARP:\n"
        "(tap to toggle, then press <b>Done</b>)",
        parse_mode="HTML",
        reply_markup=services_keyboard(_configs(context), selected),
    )
    return SELECT_SERVICES


# ------------------------------------------------------------------
# Generation
# ------------------------------------------------------------------
async def _generate(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    assert query is not None and context.user_data is not None
    configs = _configs(context)
    user = context.user_data

    await query.edit_message_text("\u23f3 Generating WARP configuration\u2026")

    try:
        account = await register_warp()
    except Exception:
        logger.exception("WARP registration failed")
        await query.edit_message_text(
            "\u274c Failed to register with Cloudflare WARP. Please try again later."
        )
        return ConversationHandler.END

    # Resolve user selections
    dns = configs.dns_servers[user["dns_idx"]]
    relay = configs.relay_servers[user["relay_idx"]]

    if user.get("routing") == "split":
        selected: set[int] = user.get("selected_svcs", set())
        allowed_ips: list[str] = []
        for idx in sorted(selected):
            allowed_ips.extend(configs.routing_services[idx].routes)
        if not allowed_ips:
            allowed_ips = ["0.0.0.0/0", "::/0"]
    else:
        allowed_ips = ["0.0.0.0/0", "::/0"]

    params = GeneratorParams(
        private_key=account.private_key,
        public_key=account.public_key,
        peer_public_key=account.peer_public_key,
        client_ipv4=account.client_ipv4,
        client_ipv6=account.client_ipv6,
        dns_servers=dns.servers,
        endpoint=relay.endpoint,
        allowed_ips=allowed_ips,
    )

    fmt = user["format"]
    generator = GENERATORS[fmt]()
    content, filename = generator.generate(params)

    # Send config as a file
    doc = BytesIO(content.encode("utf-8"))
    doc.name = filename
    assert query.message is not None
    await query.message.reply_document(
        document=doc,
        caption=(
            f"\u2705 <b>WARP config generated!</b>\n"
            f"\U0001f4c4 Format: <b>{fmt.upper()}</b>"
        ),
        parse_mode="HTML",
    )

    # AmneziaWG deep-link (sent as a file – the link is too long for a message)
    if fmt == "amnezia" and isinstance(generator, AmneziaWGGenerator):
        deeplink = generator.generate_deeplink(params)
        link_doc = BytesIO(deeplink.encode("utf-8"))
        link_doc.name = "warp-amnezia-deeplink.txt"
        await query.message.reply_document(
            document=link_doc,
            caption=(
                "\U0001f517 <b>AmneziaVPN Deep Link</b>\n"
                "Open the file and copy the <code>vpn://</code> link into AmneziaVPN."
            ),
            parse_mode="HTML",
        )

    return ConversationHandler.END


# ------------------------------------------------------------------
# /cancel
# ------------------------------------------------------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.message is not None
    await update.message.reply_text("\u274c Configuration cancelled.")
    return ConversationHandler.END


# ------------------------------------------------------------------
# Handler registration
# ------------------------------------------------------------------
def setup_handlers(app: Application) -> None:  # type: ignore[type-arg]
    """Register all handlers on *app*."""
    # Main menu / standalone handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(
        MessageHandler(filters.Text([BTN_STATUS]), warp_status)
    )
    app.add_handler(
        MessageHandler(filters.Text([BTN_HELP]), help_handler)
    )

    # Config-generation conversation
    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Text([BTN_GENERATE]), generate_entry),
        ],
        states={
            SELECT_FORMAT: [
                CallbackQueryHandler(on_format, pattern=f"^{FORMAT_CB}"),
            ],
            SELECT_DNS: [
                CallbackQueryHandler(on_dns, pattern=f"^{DNS_CB}"),
            ],
            SELECT_RELAY: [
                CallbackQueryHandler(on_relay, pattern=f"^{RELAY_CB}"),
            ],
            SELECT_ROUTING: [
                CallbackQueryHandler(on_routing, pattern=f"^{ROUTE_CB}"),
            ],
            SELECT_SERVICES: [
                CallbackQueryHandler(
                    on_service_toggle,
                    pattern=f"^{SVC_CB}",
                ),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
