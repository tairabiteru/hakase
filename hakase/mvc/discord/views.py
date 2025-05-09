from django.http import HttpResponse

from ...core.conf import Config
from ..core.utils import template
from ..core.oauth2 import require_oauth2
from ..discord.models import Guild


conf = Config.load()


@require_oauth2()
@template("user.html")
async def user(request):
    ctx = {}
    return ctx


@require_oauth2()
async def save_user(request):
    return HttpResponse("")


@require_oauth2()
@template("tags.html")
async def tags(request):
    guilds = {}
    status = ""
    for _, guild in request.bot.cache.get_guilds_view().items():
        member = guild.get_member(request.session['uid'])
        if member:
            g, _ = await Guild.objects.aget_or_create(id=guild.id)
            guilds[guild.id] = {
                'name': guild.name,
                'tag_roles': {}
            }

            roles_exist = False
            roles = []
            async for role in g.tag_roles.all():
                roles_exist = True
                role.attach_bot(request.bot)
                await role.aresolve_all()
                roles.append(role)
            
            for role in sorted(roles, key=lambda r: r.obj.name):
                guilds[guild.id]['tag_roles'][role.id] = {
                    'name': role.obj.name,
                    'color': role.obj.color.hex_code,
                    'description': role.description,
                    'enabled': role.id in member.role_ids
                }
            
            if not roles_exist:
                guilds.pop(guild.id)
    
    if request.POST:
        post_data = dict(request.POST)
        guild_id = int(post_data.pop('guild')[0])
        _ = post_data.pop('csrfmiddlewaretoken')
        new_roles = list([int(id) for id in post_data.keys()])
        guild = request.bot.cache.get_guild(guild_id)
        member = guild.get_member(request.session['uid'])
        added = 0
        removed = 0

        for role_id in member.role_ids:
            if role_id not in new_roles:
                if role_id in guilds[guild.id]['tag_roles']:
                    removed += 1
                    await member.remove_role(role_id, reason="Tag role removal.")
        
        for role_id in new_roles:
            if role_id not in member.role_ids:
                if role_id in guilds[guild.id]['tag_roles']:
                    added += 1
                    await member.add_role(role_id, reason="Tag role addition.")
        
        guild, _ = await Guild.objects.aget_or_create(id=guild.id)
        guild = await Guild.objects.select_related("tag_delimiter_role").aget(id=guild.id)

        if guild.tag_delimiter_role:
            if len(new_roles) != 0:
                if guild.tag_delimiter_role.id not in member.role_ids:
                    await member.add_role(guild.tag_delimiter_role.id, reason="Add tag delimiter role.")
            else:
                if guild.tag_delimiter_role.id in member.role_ids:
                    await member.remove_role(guild.tag_delimiter_role.id, reason="Remove tag delimiter role.")
        
        for role in guilds[guild.id]['tag_roles']:
            guilds[guild.id]['tag_roles'][role]['enabled'] = role in new_roles
        
        if added != 0 and removed != 0:
            p1 = "role" if added == 1 else "roles"
            p2 = "role" if removed == 1 else "roles"
            status = f"Added {added} {p1}, and removed {removed} {p2}."
        elif added != 0:
            p1 = "role" if added == 1 else "roles"
            status = f"Added {added} {p1}."
        elif removed != 0:
            p1 = "role" if removed != 1 else "roles"
            status = f"Removed {removed} {p1}."
            
    return {'guilds': guilds, 'status': status}