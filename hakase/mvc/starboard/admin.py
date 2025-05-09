from django.contrib import admin
from .models import Starboard
from ..discord.models import Channel, Role
from ..discord.admin import BaseDiscordForm, BaseDiscordAdmin, DiscordChoiceField, DiscordMultipleChoiceField


class StarboardForm(BaseDiscordForm):
    channel = DiscordChoiceField(queryset=Channel.objects.all())
    roles = DiscordMultipleChoiceField(queryset=Role.objects.all(), required=False)

    class Meta:
        model = Starboard
        fields = "__all__"


class StarboardAdmin(BaseDiscordAdmin):
    form = StarboardForm
    list_display = ('id', 'channel')
    

admin.site.register(Starboard, StarboardAdmin)