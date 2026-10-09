import hikari
import lightbulb

from ...lib.hooks import require_granted
from ...mvc.golmdirectory.models import Library, Member

directory = lightbulb.Group("directory", "GoLM Member Directory.")


@directory.register
class GetMember(
    lightbulb.SlashCommand,
    name="member",
    description="Show a member's profile.",
    hooks=[require_granted],
):
    name = lightbulb.string("name", "The name of the member")

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context):
        try:
            member = await Member.objects.aget(name__icontains=self.name)
            await ctx.respond(
                embed=(await member.get_embed(ctx.client.app)),
                flags=hikari.MessageFlag.EPHEMERAL,
            )
        except Member.DoesNotExist:
            await ctx.respond(
                f"No member found with the name `{self.name}`.",
                flags=hikari.MessageFlag.EPHEMERAL,
            )


@directory.register
class GetLibrary(
    lightbulb.SlashCommand,
    name="library",
    description="Show a library's profile.",
    hooks=[require_granted],
):
    name = lightbulb.string("name", "The name of the library")

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context):
        try:
            library = await Library.objects.aget(name__icontains=self.name)
            await ctx.respond(
                embed=(await library.get_embed(ctx.client.app)),
                flags=hikari.MessageFlag.EPHEMERAL,
            )
        except Library.DoesNotExist:
            await ctx.respond(
                f"No library found with the name `{self.name}`.",
                flags=hikari.MessageFlag.EPHEMERAL,
            )
