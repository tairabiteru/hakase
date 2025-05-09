import asyncio
from django.db import models
from django.forms import ValidationError
import hikari
import typing as t

from .base import DiscordBaseModel
from ..fields import ChannelIDField, GuildIDField, RoleIDField


class ChannelMapping(DiscordBaseModel):
    id = models.AutoField(primary_key=True)
    channel = ChannelIDField(help_text="The Discord channel associated with the mapping.")
    name = models.CharField(max_length=128)

    def __str__(self) -> str:
        return self.name


class RoleMapping(DiscordBaseModel):
    id = models.AutoField(primary_key=True)
    role = RoleIDField(help_text="The Discord role associated with the mapping.")
    name = models.CharField(max_length=128)

    def __str__(self) -> str:
        return self.name


class Theme(DiscordBaseModel):
    name = models.CharField(max_length=128, primary_key=True, unique=True, help_text="The name to call the theme.")
    guild = GuildIDField(help_text="The guild attached to the theme.")
    guild_name = models.CharField(max_length=128, blank=True, null=True, help_text="The name the guild should take on when the theme is applied.")
    channels = models.ManyToManyField(ChannelMapping, blank=True)
    roles = models.ManyToManyField(RoleMapping, blank=True)
    start_date = models.CharField(max_length=32, blank=True, null=True, help_text="The date when the theme should be applied.")
    end_date = models.CharField(max_length=32, blank=True, null=True, help_text="The date when the theme should be reverted.")
    default = models.BooleanField(default=False)

    async def asave(self, *args, **kwargs):
        if self.default is True:
            async for theme in Theme.objects.filter(guild=self.guild, default=True):
                if theme.default is True:
                    raise ValidationError("Only one default theme is allowed per guild.")
        return await super().asave(*args, **kwargs)

    @classmethod
    async def mint(cls, guild: hikari.Guild, name: str) -> t.Type[t.Self]:
        theme = cls(name=name, guild=guild)
        theme.guild_name = guild.name
        await theme.asave()

        for channel in guild.get_channels().values():
            mapping = ChannelMapping(
                channel=channel,
                name=channel.name
            )
            await mapping.asave()
            await theme.channels.aadd(mapping)
        
        for role in guild.get_roles().values():
            if role.name != "@everyone":
                mapping = RoleMapping(
                    role=role,
                    name=role.name
                )
                await mapping.asave()
                await theme.roles.aadd(mapping)
    
    async def apply(self, bot: hikari.GatewayBot) -> t.Tuple[int]:
        channels_changed = 0
        roles_changed = 0
        name_changed = 0
        guild = bot.cache.get_guild(self.guild)
        errors = [0, 0]

        async for mapping in self.channels.all():
            try:
                channel = await bot.rest.fetch_channel(mapping.channel)
                if channel.name != mapping.name:
                    await bot.rest.edit_channel(mapping.channel, name=mapping.name)
                    channels_changed += 1
                    await asyncio.sleep(1.0)
            except hikari.NotFoundError:
                await mapping.adelete()
            except hikari.ForbiddenError:
                errors[0] = 1
        
        async for mapping in self.roles.all():
            try:
                role = await bot.rest.fetch_role(guild, mapping.role)
                if role.name != mapping.name:
                    await bot.rest.edit_role(guild, mapping.role, name=mapping.name)
                    roles_changed += 1
                    await asyncio.sleep(1.0)
            except hikari.NotFoundError:
                await mapping.adelete()
            except hikari.ForbiddenError:
                errors[1] = 1
        
        if guild.name != self.guild_name:
            await bot.rest.edit_guild(guild, name=self.guild_name)
            name_changed = 1
        
        return name_changed, channels_changed, roles_changed, errors
            