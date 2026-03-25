"""Telegram bot handlers — conversation flow for generating WARP configs."""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict, deque
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

from bot.i18n import t_user, available_languages
from core.config import BotConfigs
from core.generators import (
    FORMATS,
    GENERATORS,
    AmneziaWGGenerator,
    GeneratorParams,
)
from core.warp import register_warp

from bot.keyboards import (
    BACK_CB,
    CONFIRM_CB,
    DNS_CB,
    FORMAT_CB,
    FORMAT_KEYS,
    GENERATE_ANOTHER_CB,
    LANG_CB,
    RELAY_CB,
    ROUTE_CB,
    SVC_CB,
    SVC_DONE_CB,
    confirm_keyboard,
    dns_keyboard,
    format_keyboard,
    generate_another_keyboard,
    language_keyboard,
    main_menu_keyboard,
    relay_keyboard,
    routing_keyboard,
    services_keyboard,
)

logger = logging.getLogger(__name__)


def _positive_int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning("Invalid %s=%r, using default %d", name, raw, default)
        return default
    if value <= 0:
        logger.warning("Invalid %s=%r, using default %d", name, raw, default)
        return default
    return value


FLOOD_WINDOW_SEC = _positive_int_env("BOT_FLOOD_WINDOW_SEC", 10)
FLOOD_MAX_EVENTS = _positive_int_env("BOT_FLOOD_MAX_EVENTS", 8)
GENERATE_COOLDOWN_SEC = _positive_int_env("BOT_GENERATE_COOLDOWN_SEC", 20)

# Conversation states
(
    SELECT_FORMAT,
    SELECT_DNS,
    SELECT_RELAY,
    SELECT_ROUTING,
    SELECT_SERVICES,
    CONFIRM,
) = range(6)


def _configs(context: ContextTypes.DEFAULT_TYPE) -> BotConfigs:
    return context.bot_data["configs"]


def _ud(context: ContextTypes.DEFAULT_TYPE) -> dict | None:
    """Shortcut to get user_data for translation."""
    return context.user_data


def _flood_state(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.bot_data.setdefault(
        "_flood_state",
        {
            "events": defaultdict(deque),
            "generate_cooldowns": {},
        },
    )


def _cleanup_flood_state(context: ContextTypes.DEFAULT_TYPE, now: float) -> None:
    state = _flood_state(context)
    events: defaultdict[int, deque[float]] = state["events"]
    cooldowns: dict[int, float] = state["generate_cooldowns"]

    threshold = now - FLOOD_WINDOW_SEC
    stale_users: list[int] = []
    for user_id, q in events.items():
        while q and q[0] < threshold:
            q.popleft()
        if not q and cooldowns.get(user_id, 0.0) <= now:
            stale_users.append(user_id)

    for user_id in stale_users:
        events.pop(user_id, None)
        cooldowns.pop(user_id, None)


def _is_flooded(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    state = _flood_state(context)
    events: defaultdict[int, deque[float]] = state["events"]
    now = time.monotonic()
    _cleanup_flood_state(context, now)
    q = events[user_id]

    threshold = now - FLOOD_WINDOW_SEC
    while q and q[0] < threshold:
        q.popleft()

    if len(q) >= FLOOD_MAX_EVENTS:
        return True

    q.append(now)
    return False


def _generate_cooldown_left(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> int:
    state = _flood_state(context)
    cooldowns: dict[int, float] = state["generate_cooldowns"]
    now = time.monotonic()
    _cleanup_flood_state(context, now)
    ready_at = cooldowns.get(user_id, 0.0)
    if ready_at > now:
        return int(ready_at - now) + 1
    return 0


def _mark_generate_cooldown(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    state = _flood_state(context)
    cooldowns: dict[int, float] = state["generate_cooldowns"]
    cooldowns[user_id] = time.monotonic() + GENERATE_COOLDOWN_SEC


# ------------------------------------------------------------------
# /start
# ------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message and show the persistent reply keyboard."""
    assert update.message is not None
    await update.message.reply_text(
        t_user("welcome", _ud(context)),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(_ud(context)),
    )


# ------------------------------------------------------------------
# "🚀 Generate Config" button  —  entry-point
# ------------------------------------------------------------------
async def generate_entry(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Show the format picker (entry-point for the conversation)."""
    assert update.message is not None
    user = update.effective_user
    if user and _is_flooded(context, user.id):
        await update.message.reply_text(t_user("flood_wait", _ud(context)))
        return SELECT_FORMAT
    await update.message.reply_text(
        t_user("step_format", _ud(context)),
        parse_mode="HTML",
        reply_markup=format_keyboard(_ud(context)),
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
        t_user("warp_status", _ud(context)),
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
        t_user("help", _ud(context)),
        parse_mode="HTML",
    )


# ------------------------------------------------------------------
# /lang — language selection
# ------------------------------------------------------------------
async def lang_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Show the language picker."""
    assert update.message is not None
    await update.message.reply_text(
        t_user("lang_prompt", _ud(context)),
        parse_mode="HTML",
        reply_markup=language_keyboard(),
    )


async def on_lang_select(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle language selection callback."""
    query = update.callback_query
    assert query is not None and query.data is not None and context.user_data is not None
    await query.answer()

    lang = query.data.removeprefix(LANG_CB)
    context.user_data["lang"] = lang

    # Show confirmation in the newly selected language
    await query.edit_message_text(
        t_user("lang_changed", context.user_data),
        parse_mode="HTML",
    )

    # Re-send the main menu keyboard with button text in the new language
    assert query.message is not None
    await query.message.reply_text(
        t_user("welcome", context.user_data),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(context.user_data),
    )


# ------------------------------------------------------------------
# Step 1 — format
# ------------------------------------------------------------------
async def on_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None and query.data is not None and context.user_data is not None
    user = update.effective_user
    if user and _is_flooded(context, user.id):
        await query.answer(text=t_user("flood_wait", _ud(context)), show_alert=False)
        return SELECT_FORMAT
    await query.answer()

    context.user_data["format"] = query.data.removeprefix(FORMAT_CB)

    await query.edit_message_text(
        t_user("step_dns", _ud(context)),
        parse_mode="HTML",
        reply_markup=dns_keyboard(_configs(context), _ud(context)),
    )
    return SELECT_DNS


# ------------------------------------------------------------------
# Step 2 — DNS
# ------------------------------------------------------------------
async def on_dns(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None and query.data is not None and context.user_data is not None
    user = update.effective_user
    if user and _is_flooded(context, user.id):
        await query.answer(text=t_user("flood_wait", _ud(context)), show_alert=False)
        return SELECT_DNS
    await query.answer()

    context.user_data["dns_idx"] = int(query.data.removeprefix(DNS_CB))

    await query.edit_message_text(
        t_user("step_relay", _ud(context)),
        parse_mode="HTML",
        reply_markup=relay_keyboard(_configs(context), _ud(context)),
    )
    return SELECT_RELAY


# ------------------------------------------------------------------
# Step 3 — relay
# ------------------------------------------------------------------
async def on_relay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None and query.data is not None and context.user_data is not None
    user = update.effective_user
    if user and _is_flooded(context, user.id):
        await query.answer(text=t_user("flood_wait", _ud(context)), show_alert=False)
        return SELECT_RELAY
    await query.answer()

    context.user_data["relay_idx"] = int(query.data.removeprefix(RELAY_CB))

    await query.edit_message_text(
        t_user("step_routing", _ud(context)),
        parse_mode="HTML",
        reply_markup=routing_keyboard(_ud(context)),
    )
    return SELECT_ROUTING


# ------------------------------------------------------------------
# Step 4 — routing mode
# ------------------------------------------------------------------
async def on_routing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None and query.data is not None and context.user_data is not None
    user = update.effective_user
    if user and _is_flooded(context, user.id):
        await query.answer(text=t_user("flood_wait", _ud(context)), show_alert=False)
        return SELECT_ROUTING
    await query.answer()

    mode = query.data.removeprefix(ROUTE_CB)

    if mode == "full":
        context.user_data["routing"] = "full"
        return await _show_confirm(update, context)

    context.user_data["routing"] = "split"
    context.user_data["selected_svcs"] = set()

    await query.edit_message_text(
        t_user("step_services", _ud(context)),
        parse_mode="HTML",
        reply_markup=services_keyboard(_configs(context), set(), _ud(context)),
    )
    return SELECT_SERVICES


# ------------------------------------------------------------------
# Step 4b — service toggle (split-tunnel)
# ------------------------------------------------------------------
async def on_service_toggle(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    assert query is not None and query.data is not None and context.user_data is not None
    user = update.effective_user
    if user and _is_flooded(context, user.id):
        await query.answer(text=t_user("flood_wait", _ud(context)), show_alert=False)
        return SELECT_SERVICES
    await query.answer()

    if query.data == SVC_DONE_CB:
        return await _show_confirm(update, context)

    idx = int(query.data.removeprefix(SVC_CB))
    selected: set[int] = context.user_data.setdefault("selected_svcs", set())

    if idx in selected:
        selected.discard(idx)
    else:
        selected.add(idx)

    await query.edit_message_text(
        t_user("step_services", _ud(context)),
        parse_mode="HTML",
        reply_markup=services_keyboard(_configs(context), selected, _ud(context)),
    )
    return SELECT_SERVICES


# ------------------------------------------------------------------
# Step 5 — confirmation
# ------------------------------------------------------------------
async def _show_confirm(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Show a summary and ask the user to confirm before generating."""
    query = update.callback_query
    assert query is not None and context.user_data is not None
    configs = _configs(context)
    user = context.user_data
    ud = _ud(context)

    fmt = user["format"]
    fmt_label = t_user(f"fmt_{fmt}", ud)
    dns_label = t_user("dns_" + configs.dns_servers[user["dns_idx"]].id, ud)
    relay_label = t_user("relay_" + configs.relay_servers[user["relay_idx"]].id, ud)

    if user.get("routing") == "split":
        selected: set[int] = user.get("selected_svcs", set())
        if selected:
            svc_names = [t_user("svc_" + configs.routing_services[i].id, ud) for i in sorted(selected)]
            routing_label = ", ".join(svc_names)
        else:
            routing_label = t_user("routing_full_label", ud)
    else:
        routing_label = t_user("routing_full_label", ud)

    await query.edit_message_text(
        t_user("step_confirm", ud, format=fmt_label, dns=dns_label, relay=relay_label, routing=routing_label),
        parse_mode="HTML",
        reply_markup=confirm_keyboard(ud),
    )
    return CONFIRM


async def on_confirm(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the confirm / back buttons."""
    query = update.callback_query
    assert query is not None and query.data is not None and context.user_data is not None
    user = update.effective_user
    if user and _is_flooded(context, user.id):
        await query.answer(text=t_user("flood_wait", _ud(context)), show_alert=False)
        return CONFIRM
    await query.answer()

    if query.data == CONFIRM_CB:
        if user:
            left = _generate_cooldown_left(context, user.id)
            if left > 0:
                await query.answer(
                    text=t_user("generation_cooldown_wait", _ud(context), seconds=left),
                    show_alert=False,
                )
                return CONFIRM
            _mark_generate_cooldown(context, user.id)
        return await _generate(update, context)

    # Back → restart the conversation from step 1
    await query.edit_message_text(
        t_user("step_format", _ud(context)),
        parse_mode="HTML",
        reply_markup=format_keyboard(_ud(context)),
    )
    return SELECT_FORMAT


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
    ud = _ud(context)

    await query.edit_message_text(t_user("generating", ud))

    try:
        account = await register_warp()
    except Exception:
        logger.exception("WARP registration failed")
        await query.edit_message_text(t_user("generation_failed", ud))
        return ConversationHandler.END

    # Resolve user selections
    dns = configs.dns_servers[user["dns_idx"]]
    relay = configs.relay_servers[user["relay_idx"]]
    fmt = user["format"] if user["format"] in FORMATS else "wireguard"

    if user.get("routing") == "split":
        selected_set: set[int] = user.get("selected_svcs", set())
        allowed_ips: list[str] = []
        for idx in sorted(selected_set):
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
        endpoint=relay.endpoint_for(fmt),
        allowed_ips=allowed_ips,
    )

    generator = GENERATORS[fmt]()
    content, filename = generator.generate(params)

    # Send config as a file
    doc = BytesIO(content.encode("utf-8"))
    doc.name = filename
    fmt_label = t_user(f"fmt_{fmt}", ud)
    assert query.message is not None
    await query.message.reply_document(
        document=doc,
        caption=t_user("config_generated", ud, format=fmt_label),
        parse_mode="HTML",
    )

    # AmneziaWG deep-link (sent as a file – the link is too long for a message)
    if fmt == "amnezia" and isinstance(generator, AmneziaWGGenerator):
        deeplink = generator.generate_deeplink(params)
        link_doc = BytesIO(deeplink.encode("utf-8"))
        link_doc.name = "warp-amnezia-deeplink.txt"
        await query.message.reply_document(
            document=link_doc,
            caption=t_user("amnezia_deeplink", ud),
            parse_mode="HTML",
        )

    # Offer to generate another config
    await query.message.reply_text(
        t_user("btn_generate", ud),
        reply_markup=generate_another_keyboard(ud),
    )
    return SELECT_FORMAT


# ------------------------------------------------------------------
# "Generate another" callback (re-enter the conversation)
# ------------------------------------------------------------------
async def on_generate_another(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Re-enter the conversation from the generate-another button."""
    query = update.callback_query
    assert query is not None and context.user_data is not None
    user = update.effective_user
    if user and _is_flooded(context, user.id):
        await query.answer(text=t_user("flood_wait", _ud(context)), show_alert=False)
        return SELECT_FORMAT
    await query.answer()

    # Clear previous selections but keep user preferences (like lang)
    for key in ("format", "dns_idx", "relay_idx", "routing", "selected_svcs"):
        context.user_data.pop(key, None)

    await query.edit_message_text(
        t_user("step_format", _ud(context)),
        parse_mode="HTML",
        reply_markup=format_keyboard(_ud(context)),
    )
    return SELECT_FORMAT


# ------------------------------------------------------------------
# /cancel
# ------------------------------------------------------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.message is not None
    await update.message.reply_text(t_user("cancelled", _ud(context)))
    return ConversationHandler.END


# ------------------------------------------------------------------
# Handler registration
# ------------------------------------------------------------------
def setup_handlers(app: Application) -> None:  # type: ignore[type-arg]
    """Register all handlers on *app*."""
    # Main menu / standalone handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("lang", lang_handler))
    app.add_handler(CallbackQueryHandler(on_lang_select, pattern=f"^{LANG_CB}"))
    app.add_handler(
        MessageHandler(filters.Regex(r"^📊"), warp_status)
    )
    app.add_handler(
        MessageHandler(filters.Regex(r"^❓"), help_handler)
    )

    # Config-generation conversation
    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^🚀"), generate_entry),
        ],
        states={
            SELECT_FORMAT: [
                CallbackQueryHandler(on_format, pattern=f"^{FORMAT_CB}"),
                CallbackQueryHandler(on_generate_another, pattern=f"^{GENERATE_ANOTHER_CB}$"),
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
            CONFIRM: [
                CallbackQueryHandler(on_confirm, pattern=f"^({CONFIRM_CB}|{BACK_CB})"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
