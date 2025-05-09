import logging.handlers
import colorlog
import logging
import os

from .conf import Config


conf: Config = Config.load()


logging.root.setLevel(logging.NOTSET)

stream_handler: colorlog.StreamHandler = colorlog.StreamHandler()
stream_handler.setLevel(conf.logging.main_level)
stream_handler.setFormatter(
    colorlog.ColoredFormatter(
        f"%(log_color)s{conf.logging.log_format}",
        datefmt=conf.logging.date_format,
        reset=True,
        log_colors = {
            'DEBUG': 'light_blue',
            'INFO': 'light_green',
            'WARNING': 'light_yellow',
            'ERROR': 'light_red',
            'CRITICAL': 'light_purple'
        }
    ) 
)

file_handler: logging.handlers.TimedRotatingFileHandler = logging.handlers.TimedRotatingFileHandler(
    os.path.join(conf.logs, "bot.log"),
    when="midnight"
)
file_handler.setLevel(conf.logging.main_level)
file_handler.setFormatter(logging.Formatter(conf.logging.log_format))

logger: logging.Logger = colorlog.getLogger()
logger.addHandler(stream_handler)
logger.addHandler(file_handler)