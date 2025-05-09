"""
Module defines the concept of a daemon.

Hakase has the ability to define "daemons," that is, routines which are
periodically executed as apart of her natural behavior in the background.
"""
import hikari

from .reminders import check_reminders


__all__ = [
    check_reminders
]


def run_daemons(bot: hikari.GatewayBot) -> None:
    """
    Begin executing all daemons.

    Args:
      bot: hikari.GatewayBot: The bot object. 

    Returns:
        None
    """
    loop = hikari.internal.aio.get_or_make_loop()

    for daemon in __all__:
        daemon = daemon()
        daemon.attach_bot(bot)
        loop.create_task(daemon.service())

        