from django.db import models
import hikari

from ..discord.models import DiscordBaseModel
from ...core.conf import Config
from ...lib.utils import utcnow


conf = Config.load()


class Reminder(DiscordBaseModel):
    user = models.ForeignKey("discord.User", null=True, on_delete=models.CASCADE, help_text="The user the reminder belongs to.")
    time = models.DateTimeField(help_text="The time at which the reminder should be sent.")
    text = models.TextField(help_text="The text which should be transmitted when the reminder time is met.")

    @classmethod
    async def check_reminders(cls, bot):
        async for reminder in cls.objects.all():
            reminder = await cls.objects.select_related("user").aget(id=reminder.id)
            if reminder.time <= utcnow():
                await reminder.remind(bot)

    async def remind(self, bot):
        self.user.attach_bot(bot)
        await self.user.aresolve_all()
        await self.user.obj.send(self.get_embed())
        await self.adelete()
    
    def get_embed(self):
        embed = hikari.Embed(
            title="Reminder!",
            description=self.text
        )
        embed.set_thumbnail("https://cdn-icons-png.flaticon.com/512/1792/1792931.png")
        return embed

    
    



