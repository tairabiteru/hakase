import hikari

from ..lib.daemon import daemon
from ..mvc.reminders.models import Reminder


@daemon(seconds=5)
async def check_reminders(bot: hikari.GatewayBot) -> None:
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
    await Reminder.check_reminders(bot)