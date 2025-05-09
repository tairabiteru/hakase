from django.db import models

from .base import DiscordBaseModel
from ..fields import UserIDField
from ....lib.permissions import PermissionState
import hikari


class User(DiscordBaseModel):
    id = UserIDField(primary_key=True, help_text="The Discord ID of this user.")
    acl = models.ManyToManyField("discord.PermissionsObject", blank=True, help_text="The Access Control List of this user, determining their permissions.")
    stopwatch = models.DateTimeField(null=True, default=None, blank=True, help_text="The last time this user's stopwatch was started.")

    last_choices_list = models.JSONField(default=list, blank=True, help_text="The last set of choices used in the /choose command.")
    last_choice = models.TextField(null=True, blank=True, help_text="The last choice the bot made in the /choose command.")
    last_choice_time = models.DateTimeField(null=True, default=None, blank=True, help_text="The last time the /choose command was run.")
    
    locale_settings = models.OneToOneField("discord.Locale", on_delete=models.PROTECT, null=True, default=None)

    administrative_notes = models.TextField(blank=True, null=True)

    @property
    def obj(self):
        try:
            if self._resolved['id'] is None:
                return None
            if isinstance(self._resolved['id'], Exception):
                raise self._resolved['id']
            return self._resolved['id']
        except KeyError:
            raise ValueError("resolve_all() must be called before accessing.")
    
    async def get_acl(self, root):
        acl = {}
        async for obj in self.acl.all():
            node = root.get_node(obj.node)
            setting = PermissionState.DENY if obj.setting == "-" else PermissionState.ALLOW
            acl[node] = setting
        return acl 
    
    def save(self, *args, **kwargs):
        from .locale import Locale
        o2o_fields = {
            'locale_settings': Locale
        }
        for field, cls in o2o_fields.items():
            if getattr(self, field) is None:
                o = cls()
                o.save()
                setattr(self, field, o)
        return super().save(*args, **kwargs)
    
    async def asave(self, *args, **kwargs):
        from .locale import Locale
    
        o2o_fields = {
            'locale_settings': Locale
        }

        for field, cls in o2o_fields.items():
            try:
                s = await User.objects.select_related(field).aget(id=self.id)
                if getattr(s, field) is None:
                    o = cls()
                    await o.asave()
                    setattr(self, field, o)
            except User.DoesNotExist:
                o = cls()
                await o.asave()
                setattr(self, field, o)
        return await super().asave(*args, **kwargs)
    
    def __str__(self):
        try:
            return f"{self.obj.username}#{self.obj.discriminator}"
        except ValueError: 
            return f"UID: {self.id}"
        except AttributeError:
            return f"UID: {self.id} (Not in cache)"
    
    async def fetch_acl(self):
        acl = {}
        async for obj in self.acl.all():
            acl[obj.node] = obj.setting
        return acl
    
    async def localnow(self):
        locale = (await User.objects.select_related("locale_settings").aget(id=self.id)).locale_settings
        return locale.localnow()
    
    async def aslocaltime(self, dt):
        locale = (await User.objects.select_related("locale_settings").aget(id=self.id)).locale_settings
        return locale.aslocaltime(dt)
    
    async def aslocaltimestamp(self, dt):
        locale = (await User.objects.select_related("locale_settings").aget(id=self.id)).locale_settings
        dt = locale.aslocaltime(dt)
        return dt.strftime(locale.datetime_format)
    
    @property
    def locale(self):
        return self.locale_settings
    
    async def render_profile_embed(self, ctx):
        embed = hikari.Embed(title=f"__{self.obj.username}__")
        embed.set_thumbnail(self.obj.avatar_url)
        self_locale = (await User.objects.select_related("locale_settings").aget(id=self.id)).locale_settings
        author, _ = await User.objects.select_related("locale_settings").aget_or_create(id=ctx.user.id)
        user_locale = author.locale_settings

        if self.birthday is not None:
            embed.add_field(name="Birthday", value=self.birthday.strftime(user_locale.date_format))
        
        embed.add_field(name="Timezone", value=self_locale.timezone)
        if self_locale.location is not None:
            embed.add_field(name="Location", value=self_locale.location)
        return embed