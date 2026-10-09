import hikari
from django.db import models

from ...core.models import BaseAsyncModel
from .member import Member

from ....core.conf import Config


conf = Config.load()


class Library(BaseAsyncModel):
    name = models.CharField(max_length=256, blank=False, unique=True)
    address = models.TextField(blank=False, unique=True)

    class Meta:
        verbose_name_plural = "libraries"

    def __str__(self) -> str:
        return str(self.name)

    @classmethod
    async def handle_lib_mention_event(cls, event: hikari.events.GuildMessageCreateEvent) -> None:
        for rid in conf.vars.library_mention_roles:
            if rid in event.member.role_ids:
                break
        else:
            return

        contained_libs = []
        async for library in cls.objects.all():
            if event.content is not None:
                if f"@{library.name}" in event.content:
                    contained_libs.append(library)

        if not contained_libs:
            return

        mentions = []
        for library in contained_libs:
            mentions += await library.get_mentions(event.app)

        mentions = list(dict.fromkeys(mentions))
        msg = ""
        for mention in mentions:
            msg += f"{mention} "

        await event.app.rest.create_message(event.channel_id, msg, reply=event.message)

    async def get_mentions(self, bot: hikari.GatewayBot) -> str:
        mentions = []
        async for member in self.member_set.select_related("user"):
            member.user.attach_bot(bot)
            await member.user.aresolve_all()
            mentions.append(member.user.obj.mention)
        return mentions

    async def get_embed(self, bot: hikari.GatewayBot) -> hikari.Embed:
        embed = hikari.Embed(title=str(self.name), description=str(self.address))
        members = []
        async for member in Member.objects.all():
            async for lib in member.libraries.all():
                if lib.id == self.id:
                    members.append(member)
                    break

        if members:
            embed.add_field(name="Members", value=", ".join(str(m) for m in members))
        else:
            embed.add_field(name="Members", value="No members")
        return embed
