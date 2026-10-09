import hikari
from django.db import models

from ....core.conf import Config
from ...discord.models.base import DiscordBaseModel

conf = Config.load()


class Member(DiscordBaseModel):
    user = models.OneToOneField("discord.User", on_delete=models.CASCADE, unique=True)
    name = models.CharField(max_length=256, blank=False)
    libraries = models.ManyToManyField("golmdirectory.Library", blank=True)

    def __str__(self) -> str:
        return str(self.name)

    async def get_embed(self, bot: hikari.GatewayBot) -> hikari.Embed:
        embed = hikari.Embed(title=str(self.name))
        self = await Member.objects.select_related("user").aget(pk=self.pk)
        embed.set_thumbnail((await bot.rest.fetch_user(self.user.id)).avatar_url)
        embed.add_field(name="User", value=f"<@{self.user.id}>")

        libraries = []
        async for library in self.libraries.all():
            libraries.append(str(library))
        embed.add_field(
            name="Libraries",
            value=", ".join(libraries),
        )
        return embed
