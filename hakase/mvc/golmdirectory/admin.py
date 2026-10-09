from django.contrib import admin

from ..discord.admin import BaseDiscordAdmin, BaseDiscordForm, DiscordChoiceField
from ..discord.models import User
from .models import Library, Member


class MembersForm(BaseDiscordForm):
    user = DiscordChoiceField(queryset=User.objects.all(), required=True)

    class Meta:
        model = Member
        fields = "__all__"


class MemberAdmin(BaseDiscordAdmin):
    form = MembersForm


admin.site.register(Member, MemberAdmin)
admin.site.register(Library)
