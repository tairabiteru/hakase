"""
Injection functions for the ORM.

These functions are all designed to work with Lightbulb 3's
DI system. Their purpose is to, given a context, retrieve an object
from the database associated with that object.
"""
import lightbulb

from ...mvc.discord.models import User, Channel, Guild, Locale
from ...mvc.internal.models import Revision


async def get_user(ctx: lightbulb.Context) -> User:
    """
    Resolve the author of a command into a user from the ORM.

    Parameters
    ----------
    ctx : lightbulb.Context
        The context of the command that was run.
    
    Returns
    -------
    mvc.discord.models.User
        The ORM user matching the author of the context.
    """
    return await User.objects.aget(id=ctx.user.id)


async def get_guild(ctx: lightbulb.Context) -> Guild:
    """
    Resolve the context of a command into a guild from the ORM.

    Parameters
    ----------
    ctx : lightbulb.Context
        The context of the command that was run.
    
    Returns
    -------
    mvc.discord.models.Guild
        The ORM guild matching the guild of the context.
    """
    return await Guild.objects.aget(id=ctx.guild_id)


async def get_channel(ctx: lightbulb.Context) -> Channel:
    """
    Resolve the context of a command into a channel from the ORM.

    Parameters
    ----------
    ctx : lightbulb.Context
        The context of the command that was run.
    
    Returns
    -------
    mvc.discord.models.Channel
        The ORM channel matching the channel of the context.
    """
    return await Channel.objects.aget(id=ctx.channel_id)


async def get_revision(ctx: lightbulb.Context) -> Revision:
    """
    Obtain the latest bot revision from the ORM.

    Parameters
    ----------
    ctx : lightbulb.Context
        The context of the command that was run.
    
    Returns
    -------
    mvc.internal.models.Revision
        The bot's latest revision.
    """
    return await Revision.objects.alatest()


async def get_locale(ctx: lightbulb.Context) -> Locale:
    """
    Obtain the locale of the author of the command.

    Parameters
    ----------
    ctx : lightbulb.Context
        The context of the command that was run.
    
    Returns
    -------
    mvc.discord.models.Locale
        The locale of the user who ran the command.
    """
    user = await User.objects.select_related("locale_settings").aget(id=ctx.user.id)
    return user.locale_settings

