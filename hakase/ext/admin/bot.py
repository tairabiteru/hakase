import hikari
import lightbulb
import platform
import sys

from ...core.conf import Config
from ...lib.utils import get_byte_unit, get_dir_size
from ...mvc.internal.models import Revision


conf = Config.load()
bot = lightbulb.Group("bot", f"Commands related to {conf.name}.")


@bot.register
class Info(
    lightbulb.SlashCommand,
    name="info",
    description="View information."
):
    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context, version: Revision) -> None:
        latency = round((ctx.client.app.heartbeat_latency * 1000), 1)
        frequency = round(1000.0 / latency, 5)
        python_version = ".".join(map(str, sys.version_info[0:3]))

        embed = hikari.Embed(title=conf.name, url=f"https://{conf.mvc.allowed_hosts[0]}")
        embed.description = f"**Version {version.full_version}**\nRunning on {platform.python_implementation()} {python_version}"
        embed.set_thumbnail(ctx.client.app.get_me().avatar_url)

        lines = "{:,}".format(version.lines)
        chars = "{:,}".format(version.chars)

        embed.add_field("Code Statistics", value=f"Lines: {lines}\nChars: {chars}")

        root = get_byte_unit(get_dir_size(conf.root))
        temp = get_byte_unit(get_dir_size(conf.temp))
        logs = get_byte_unit(get_dir_size(conf.logs))
        dirs = f"Root: {root}\nTemp: {temp}\nLogs: {logs}"
        embed.add_field("Directory Info", value=dirs)

        heartbeat_info = f"Period: {latency} ms\nFrequency: {frequency} Hz"
        embed.add_field("Heartbeat Info", value=heartbeat_info)
        await ctx.respond(embed)