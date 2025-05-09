import lightbulb

from .bot import bot
from .permissions import permissions
from .theme import theme


admin = lightbulb.Loader()


admin.command(bot)
admin.command(permissions)
admin.command(theme)