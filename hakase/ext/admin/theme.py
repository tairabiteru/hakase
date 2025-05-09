import lightbulb

from ...core.conf import Config
from ...lib.hooks import require_owner
from ...lib.ctx import DelayedResponse
from ...mvc.discord.models import Theme


theme = lightbulb.Group("theme", "Commands related themes.")
conf = Config.load()


@theme.register
class MintCommand(
    lightbulb.SlashCommand,
    name="mint",
    description="Mint a new theme from the current status of a server.",
    hooks=[require_owner]
):
    
    name = lightbulb.string("name", "The name of the theme.")

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        try:
            await Theme.objects.aget(name=self.name)
            await ctx.respond(f"A theme named `{self.name}` already exists.")
            return
        except Theme.DoesNotExist:
            await Theme.mint(ctx.client.app.cache.get_guild(ctx.guild_id), self.name)
            await ctx.respond(f"Minted theme using the current guild settings named `{self.name}`.")


@theme.register
class ApplyCommand(
    lightbulb.SlashCommand,
    name="apply",
    description="Apply a theme from to the server.",
    hooks=[require_owner]
):
    
    name = lightbulb.string("name", "The name of the theme.")

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        async with DelayedResponse(ctx, "Changing theme", timeout=120) as response:
            try:
                theme = await Theme.objects.aget(name=self.name)
                name, channels, roles, errors = await theme.apply(ctx.client.app)
                c_plural = "channel" if channels == 1 else "channels"
                r_plural = "role" if roles == 1 else "roles"
                msg = f"Switched to the `{theme.name}` theme. The following was updated:\n```- Changed {channels} {c_plural}\n- Changed {roles} {r_plural}"
                if name == 1:
                    msg += "\n- Guild name changed"
                msg += "```"
                
                if errors[0]:
                    msg += "Some channels could not be changed because I lack the appropriate permissions to change them.\n"
                if errors[1]:
                    msg += "Some roles could not be changed because I lack the appropriate permissions to change them.\n"

                await response.complete(msg)
            except Theme.DoesNotExist:
                await response.complete(f"A theme named {self.name} does not exist.")