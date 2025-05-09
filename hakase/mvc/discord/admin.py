from django.contrib import admin
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from ..discord.models import User, Guild, Role, Channel, DiscordBaseModel, Locale, PermissionsObject, RoleGroup, Theme, ChannelMapping, RoleMapping


class DiscordChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        obj._bot = self.request.bot
        obj.resolve_all()
        return super().label_from_instance(obj)


class DiscordMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        obj._bot = self.request.bot
        obj.resolve_all()
        return super().label_from_instance(obj)


class BaseDiscordForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = self.__class__.request
        for field in self.declared_fields.keys():
            if isinstance(self.declared_fields[field], DiscordChoiceField) or isinstance(self.declared_fields[field], DiscordMultipleChoiceField):
                self.declared_fields[field].request = self.request
        super().__init__(*args, **kwargs)

    class Meta:
        fields = '__all__'


class BaseDiscordAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        self.request = request
        return super().get_queryset(request)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj=obj, **kwargs)
        form.request = request
        return form
    
    def get_readonly_fields(self, request, obj):
        if obj is None:
            return super().get_readonly_fields(request, obj)

        obj._bot = request.bot
        obj.resolve_all()

        for name in obj._get_field_expression_map(obj._meta).keys():
            field = getattr(obj, name)
            if isinstance(field, DiscordBaseModel):
                field._bot = request.bot
                field.resolve_all()

        return super().get_readonly_fields(request, obj)


class UserForm(BaseDiscordForm):
    class Meta:
        model = User
        fields = "__all__"


class UserAdmin(BaseDiscordAdmin):
    list_display = ('name', 'id')
    form = UserForm
    readonly_fields = ('id', 'locale_settings')

    def name(self, obj):
        obj._bot = self.request.bot
        obj.resolve_all()
        try:
            return f"{obj.obj.username}#{obj.obj.discriminator}"
        except AttributeError:
            return f"Deleted UID: {obj.id}"


class GuildForm(BaseDiscordForm):
   assign_on_join = DiscordMultipleChoiceField(queryset=Role.objects.all(), required=False, widget=FilteredSelectMultiple(verbose_name=Role._meta.verbose_name, is_stacked=False))
   tag_roles = DiscordMultipleChoiceField(queryset=Role.objects.all(), required=False, widget=FilteredSelectMultiple(verbose_name=Role._meta.verbose_name, is_stacked=False))

   class Meta:
       model = Guild
       fields = "__all__"


class GuildAdmin(BaseDiscordAdmin):
    list_display = ('name', 'id')
    form = GuildForm
    readonly_fields = ('id',)
    filter_horizontal = ("assign_on_join", "tag_roles")

    def name(self, obj):
        obj._bot = self.request.bot
        obj.resolve_all()
        return obj.obj.name


class ChannelForm(BaseDiscordForm):
    guild = DiscordChoiceField(queryset=Guild.objects.all())

    class Meta:
        model = Channel
        fields = "__all__"


class ChannelAdmin(BaseDiscordAdmin):
    form = ChannelForm
    list_display = ('name', 'id', 'guild_name')
    readonly_fields = ('id', 'guild', 'type')

    def name(self, obj):
        obj._bot = self.request.bot
        obj.resolve_all()
        if obj.obj is None:
            return f"#{obj.id}"
        return obj.obj.name
    
    def guild_name(self, obj):
        obj.guild._bot = self.request.bot
        obj.guild.resolve_all()
        return obj.guild.obj.name



class RoleForm(BaseDiscordForm):
    guild = DiscordChoiceField(queryset=Guild.objects.all())

    class Meta:
        model = Role
        fields = "__all__"


class RoleAdmin(BaseDiscordAdmin):
    list_display = ('name', 'id', 'guild_name')
    form = RoleForm
    readonly_fields = ('id', 'guild')

    def name(self, obj):
        obj._bot = self.request.bot
        obj.resolve_all()
        return obj.obj.name
    
    def guild_name(self, obj):
        obj.guild._bot = self.request.bot
        obj.guild.resolve_all()
        return obj.guild.obj.name


class RoleGroupForm(BaseDiscordForm):
    watched_roles = DiscordMultipleChoiceField(queryset=Role.objects.all(), required=False, widget=FilteredSelectMultiple(verbose_name=Role._meta.verbose_name, is_stacked=False))
    header_role = DiscordChoiceField(queryset=Role.objects.all(), required=False)

    class Meta:
        model = RoleGroup
        fields = "__all__"


class RoleGroupAdmin(BaseDiscordAdmin):
    list_display = ('name', 'header_role')
    form = RoleGroupForm
    readonly_fields = ('guild',)


class ThemeForm(BaseDiscordForm):
    guild = DiscordChoiceField(Guild.objects.all())


class ThemeAdmin(BaseDiscordAdmin):
    list_display = ('name', 'guild_name')
    form = ThemeForm
    readonly_fields = ('guild',)

    def guild_name(self, obj):
        guild = self.request.bot.cache.get_guild(obj.guild)
        return guild.name


class ChannelMappingForm(BaseDiscordForm):
    channel = DiscordChoiceField(Channel.objects.all())


class ChannelMappingAdmin(BaseDiscordAdmin):
    list_display = ('id', 'channel_name', 'name')
    form = ChannelMappingForm
    readonly_fields = ('channel',)

    def channel_name(self, obj):
        channel = self.request.bot.cache.get_guild_channel(obj.channel)
        return channel.name


class RoleMappingForm(BaseDiscordForm):
    role = DiscordChoiceField(Role.objects.all())


class RoleMappingAdmin(BaseDiscordAdmin):
    list_display = ('id', 'role_name', 'name')
    form = RoleMappingForm
    readonly_fields = ('role',)

    def role_name(self, obj):
        role = self.request.bot.cache.get_role(obj.role)
        return role.name


admin.site.register(User, UserAdmin)
admin.site.register(Guild, GuildAdmin)
admin.site.register(Channel, ChannelAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Locale)
admin.site.register(PermissionsObject)
admin.site.register(RoleGroup, RoleGroupAdmin)
admin.site.register(Theme, ThemeAdmin)
admin.site.register(ChannelMapping, ChannelMappingAdmin)
admin.site.register(RoleMapping, RoleMappingAdmin)