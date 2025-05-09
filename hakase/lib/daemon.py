"""Module defining daemons

Daemons, with regard to Hakase, are background tasks. The module
that follows defines the behavior of them, as well as interfaces
for Hakase to interact with them, and shut them down when need be.
Most daemons are defined within core.bot.

    * Daemon - Class abstracting a daemon
    * daemon - Decorator which turns a function into a daemon with the specific execution period
"""

import asyncio
import hikari
import typing as t


class Daemon:
    ALL = []

    def __init__(self,
        callback: t.Coroutine,
        seconds: int,
        *args: t.Any,
        **kwargs: t.Any
    ):
        self.callback: t.Coroutine = callback
        self.args = args
        self.kwargs = kwargs
        self.seconds: int = seconds
        self._bot: t.Optional[hikari.GatewayBot] = None
    
    def attach_bot(self, bot: hikari.GatewayBot) -> None:
        self._bot = bot
    
    @property
    def bot(self) -> hikari.GatewayBot:
        if not self._bot:
            raise ValueError("Bot not attached.")
        return self._bot
    
    async def service(self) -> None:
        while True:
            await self.callback(self.bot, *self.args, **self.kwargs)
            await asyncio.sleep(self.seconds)


def daemon(seconds: int=0, minutes: int=0, hours: int=0, days: int=0) -> t.Callable:
    seconds = seconds + (minutes * 60) + (hours * 3600) + (days * 86400)
    if seconds <= 0:
        raise ValueError("The total time for a daemon's execution cannot be 0.")
    
    def inner(func) -> t.Callable:
        def inner_inner(*args, **kwargs) -> Daemon:
            return Daemon(func, seconds, *args, **kwargs)
        Daemon.ALL.append(inner_inner)
        return inner_inner
    return inner