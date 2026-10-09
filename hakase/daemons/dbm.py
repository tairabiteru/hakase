from django.db import close_old_connections
import hikari

from ..lib.daemon import daemon


@daemon(seconds=60)
async def close_old_db_connections(bot: hikari.GatewayBot) -> None:
    """
    Perform a global check for all reminders. The execution of this daemon
    is responsible for the bot knowing when a reminder's time has arrived,
    and whether or not they should notify the user.

    Args:
      bot: hikari.GatewayBot: The bot object. 

    Returns:
        None
    """
    await bot.is_ready.wait()
    close_old_connections()