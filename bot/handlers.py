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
)

from bot.config import BotConfigs
from bot.generators import (
    GENERATORS,
    AmneziaWGGenerator,
    GeneratorParams,
)
from bot.keyboards import (
    DNS_CB,
    FORMAT_CB,
    RELAY_CB,
    ROUTE_CB,
    SVC_CB,
    SVC_DONE_CB,
    dns_keyboard,
    format_keyboard,
    relay_keyboard,
    routing_keyboard,
    services_keyboard,
)
from bot.warp import register_warp

logger = logging.getLogger(__name__)

# Conversation states
SELECT_FORMAT, SELECT_DNS, SELECT_RELAY, SELECT_ROUTING, SELECT_SERVICES = range(5)


def _configs(context: ContextTypes.DEFAULT_TYPE) -> BotConfigs:
    return context.bot_data["configs"]


# ------------------------------------------------------------------
# /start
# ------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send welcome message and show the format picker."""
    text = (
        "\U0001f310 *WARP Config Generator*\n\n"
        "Generate Cloudflare WARP VPN configurations in multiple formats.\n\n"
        "Select the output format:"
    )
    assert update.message is not None
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=format_keyboard(),
    )
    return SELECT_FORMAT


# ------------------------------------------------------------------
# Step 1 — format
# ------------------------------------------------------------------
async def on_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None and query.data is not None and context.user_data is not None
    await query.answer()

    context.user_data["format"] = query.data.removeprefix(FORMAT_CB)

    await query.edit_message_text(
        "\U0001f310 Select a DNS server:",
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
        "\U0001f4e1 Select a relay server (endpoint):",
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
        "\U0001f500 Select routing mode:",
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
        "(tap to toggle, then press Done)",
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
        "(tap to toggle, then press Done)",
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
        caption=f"\u2705 WARP config generated!\n\U0001f4c4 Format: *{fmt.upper()}*",
        parse_mode="Markdown",
    )

    # AmneziaWG deep-link (sent as a file – the link is too long for a message)
    if fmt == "amnezia" and isinstance(generator, AmneziaWGGenerator):
        deeplink = generator.generate_deeplink(params)
        link_doc = BytesIO(deeplink.encode("utf-8"))
        link_doc.name = "warp-amnezia-deeplink.txt"
        await query.message.reply_document(
            document=link_doc,
            caption="\U0001f517 *AmneziaVPN Deep Link*\nOpen the file and copy the `vpn://` link into AmneziaVPN.",
            parse_mode="Markdown",
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
    """Register the conversation handler on *app*."""
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
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
