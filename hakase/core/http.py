from django.core.management import execute_from_command_line
import hikari
import logging
import os
import hikari.internal
import uvicorn

from .conf import Config
from ..lib.utils import port_in_use


conf: Config = Config.load()


uvicorn.config.LOGGING_CONFIG['formatters']['default']['fmt'] = conf.logging.log_format
uvicorn.config.LOGGING_CONFIG['formatters']['default']['use_colors'] = True
uvicorn.config.LOGGING_CONFIG['formatters']['access']['fmt'] = conf.logging.log_format
uvicorn.config.LOGGING_CONFIG['formatters']['access']['use_colors'] = True
uvicorn.config.LOGGING_CONFIG['handlers']['file'] = {
    'formatter': 'access',
    '()': lambda: logging.handlers.TimedRotatingFileHandler(
        os.path.join(conf.logs, "access.log"),
        when="midnight"
    )
}
uvicorn.config.LOGGING_CONFIG['loggers']['uvicorn.access']['handlers'] = ['file']


class HTTPDaemon(uvicorn.Server):
    """
    The bot's internal HTTP Daemon.

    This is just a Uvicorn server, but we overload some stuff here
    to stop the signal handlers from working.
    """
    def install_signal_handlers(self) -> None:
        """Overload this because they mess with the signal handlers."""
        pass
    
    async def shutdown(self, *args, **kwargs) -> None:
        """Shutdown webserver."""
        return await super().shutdown(*args, **kwargs)

    async def serve(self, *args, **kwargs) -> None:
        """Serve the webserver."""
        return await super().serve(*args, **kwargs)
    
    @classmethod
    async def run(cls, bot: hikari.GatewayBot):
        """Run the webserver."""
        if port_in_use(conf.mvc.port):
            bot.logger.error(f"HTTP Daemon failed to start on {conf.mvc.host}:{conf.mvc.port}. It is already in use.")
            return
        
        execute_from_command_line(["", "collectstatic", "--noinput"])

        loop = hikari.internal.aio.get_or_make_loop()
        loop.bot = bot

        config: uvicorn.Config = uvicorn.Config(
            f"{conf.name.lower()}.mvc.core.asgi:application",
            host=conf.mvc.host,
            port=conf.mvc.port,
            log_level=conf.logging.mvc_level.lower(),
            loop=loop
        )

        http_daemon = cls(config)
        loop.create_task(http_daemon.serve())

        bot.logger.info(f"Started internal ASGI webserver on {conf.mvc.host}:{conf.mvc.port}.")
        return http_daemon



