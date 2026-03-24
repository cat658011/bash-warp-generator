"""Entry-point: ``python -m bot``."""

from __future__ import annotations

import logging
import os

from telegram.ext import Application

from bot.config import load_configs
from bot.handlers import setup_handlers


def main() -> None:
    """Start the Telegram bot."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    logger = logging.getLogger(__name__)

    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not set. "
            "Create a bot via @BotFather and export BOT_TOKEN."
        )

    configs = load_configs()
    logger.info(
        "Loaded %d DNS servers, %d relay servers, %d routing services",
        len(configs.dns_servers),
        len(configs.relay_servers),
        len(configs.routing_services),
    )

    app = Application.builder().token(token).build()
    app.bot_data["configs"] = configs

    setup_handlers(app)

    logger.info("Bot is starting…")
    app.run_polling()


if __name__ == "__main__":
    main()
