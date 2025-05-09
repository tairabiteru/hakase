from ..discord.models import DiscordBaseModel, Guild
from django.db import models


import hikari


class Starboard(DiscordBaseModel):
    channel = models.ForeignKey("discord.Channel", on_delete=models.CASCADE, limit_choices_to={'type': 'GUILD_TEXT'}, help_text="The channel to send this starboard's messages to.")
    emoji = models.CharField(max_length=32, default="⭐🌟🌠", help_text="The emoji whose reactions activate this starboard.")
    message = models.TextField(default="☄️ Among the Stars ☄️", help_text="The message sent along with the starboard message to the aforementioned channel.")
    roles = models.ManyToManyField("discord.Role", help_text="The roles capable of using this starboard.")

    @classmethod
    async def process_event(cls, event):
        await event.app.is_ready.wait()

        guild, _ = await Guild.objects.aget_or_create(id=event.guild_id)

        if isinstance(event, hikari.GuildReactionAddEvent):
            async for starboard in guild.starboards.all():
                starboard = await Starboard.objects.select_related("channel").aget(id=starboard.id)
                if event.emoji_name in starboard.emoji:
                    async for role in starboard.roles.all():
                        if role.id in event.member.role_ids:
                            break
                    else:
                        continue
                else:
                    break
                await starboard.create_message(event.app, event.guild_id, event.channel_id, event.message_id)
    
    async def create_message(self, bot, guild_id, channel_id, message_id):
        message = await bot.rest.fetch_message(channel_id, message_id)
        embed = hikari.Embed(description=message.content)

        if message.attachments:
            file = message.attachments[0]
            if file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp', 'webm')):
                embed.set_image(file.url)
            else:
                embed.add_field(name="Attachment", value=f"[{file.filename}]({file.url})")
        
        embed.add_field(name="Original", value=f"[Jump to Original]({message.make_link(guild_id)})")

        member = bot.cache.get_member(guild_id, message.author.id)
        name = member.nickname if member.nickname else message.author.username
        embed.set_author(name=name, url=str(message.author.avatar_url))
        embed.timestamp = message.timestamp

        return await bot.rest.create_message(
            self.channel.id,
            self.message,
            embed=embed
        )
