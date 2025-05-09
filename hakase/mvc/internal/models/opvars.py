from django.db import models

from ...discord.models import DiscordBaseModel, Channel
from ....lib.utils import utcnow


class OperationalVariables(DiscordBaseModel):
    reinit_timestamp = models.DateTimeField(null=True, blank=True, default=None, help_text="The time when reinitialization took place.")
    reinit_channel = models.ForeignKey("discord.Channel", null=True, on_delete=models.SET_NULL, blank=True, default=None, help_text="The channel reinitialization was initiated in.")
    reinit_message = models.BigIntegerField(null=True, blank=True, default=None, help_text="The Discord ID of the message sent just before reinitialization.")

    class Meta:
        verbose_name_plural = "operational variables"
    
    @classmethod
    async def aget(cls, select_related=[]):
        while True:
            try:
                self = await cls.objects.select_related(*select_related).aget(id=1)
                break
            except cls.DoesNotExist:
                self = cls()
                await self.asave()

        return self
    
    @classmethod
    async def set_for_reinit(cls, channel=None, message=None):
        opvars = await cls.aget()
        if channel is not None:
            opvars.reinit_channel = await Channel.objects.aget(id=channel.id)
        if message is not None:
            opvars.reinit_message = message.id
        opvars.reinit_timestamp = utcnow()
        await opvars.asave()
    
    @classmethod
    async def clear_for_reinit(cls):
        opvars = await cls.aget()
        opvars.reinit_channel = None
        opvars.reinit_message = None
        opvars.reinit_timestamp = None
        await opvars.asave()