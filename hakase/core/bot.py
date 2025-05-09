import aiofile
import asyncio
import datetime
import hikari
import lightbulb
import logging
import lolpython
import miru
import os
import pyfiglet
import typing as t
import zoneinfo

from .log import logger
from .http import HTTPDaemon
from .conf import Config
from ..lib.utils import utcnow
from ..lib.injection import load_injection_for_commands
from ..lib.permissions import Node, AccessIsDenied
from ..lib.hooks import require_not_denied
from ..lib.utils import strfdelta
from ..daemons import run_daemons
from ..mvc.discord.hooks import DiscordEventHandler
from ..mvc.discord.models import Channel, RoleGroup
from ..mvc.internal.models import OperationalVariables, Revision
from ..mvc.starboard.models import Starboard


class Bot(hikari.GatewayBot):
    def __init__(self, conf):
        self.conf: Config = conf
        super().__init__(conf.token, intents=hikari.Intents.ALL)

        # Bot attributes
        self.logger: logging.Logger = logger
        self.is_ready: asyncio.Event = asyncio.Event()
        self.last_instantiation: datetime.datetime = self.localnow()
        self.last_connection: t.Optional[datetime.datetime] = None
        self._revision: t.Optional[Revision] = None
        self._permissions_root: t.Optional[Node] = None

        # Handle lightbulb
        self.lightbulb: lightbulb.Client = lightbulb.client_from_app(self, hooks=[require_not_denied])
        self.lightbulb.error_handler(self._on_exc_pipeline_error)
        
        # Handle miru
        self.miru: miru.Client = miru.Client(self)

        # Handle HTTP Daemon
        self.http_daemon: t.Optional[HTTPDaemon] = None

        # Define events
        self.subscribe(hikari.StartingEvent, self._load_command_handler)
        self.subscribe(hikari.ShardReadyEvent, self._on_ready)

        # These events allow the MVC to handle Discord objects.
        self.subscribe(hikari.GuildEvent, DiscordEventHandler.handle_guild_event)
        self.subscribe(hikari.MemberEvent, DiscordEventHandler.handle_member_event)
        self.subscribe(hikari.ChannelEvent, DiscordEventHandler.handle_channel_event)
        self.subscribe(hikari.RoleEvent, DiscordEventHandler.handle_role_event)

        # These events allow the MVC to track guild activity.
        self.subscribe(hikari.MemberUpdateEvent, RoleGroup.process_event)
        self.subscribe(hikari.GuildReactionAddEvent, Starboard.process_event)

    async def _load_command_handler(self, _) -> None:
        """Load Lightbulb."""
        await self.lightbulb.load_extensions("hakase.ext")

        await self.lightbulb.start()
        load_injection_for_commands(self.lightbulb)
    
    async def _on_exc_pipeline_error(self, exc: lightbulb.exceptions.ExecutionPipelineFailedException) -> bool:
        """
        Callback for execution pipeline errors.
        
        These occur when execution of a command fails for whatever reason.
        """
        if isinstance(exc.causes[0], AccessIsDenied):
            await exc.context.respond(exc.causes[0].message)
            return True
        return False

    async def _on_reinit(self) -> None:
        """
        Handle reinitialization condition.

        The bulk of the code in here only fires under the condition that
        hakase has been reinitialized. If this is the case, the timestamp
        field in her operational variables will not be null. This is what
        allows her to know whether or not this is a *RE*initialization, and
        also what allows her to know how long it took, and what channel
        this information should be sent to.
        """
        opvars = await OperationalVariables.aget(select_related=["reinit_channel"])
        if opvars.reinit_timestamp is not None:
            elapsed = utcnow() - opvars.reinit_timestamp
            elapsed = strfdelta(elapsed, '{%M}:{%S}')
            timestamp = opvars.reinit_timestamp.astimezone(self.timezone)
            timestamp = timestamp.strftime("%x %X %Z")
            revision = await Revision.objects.alatest()

            if opvars.reinit_channel is not None:
                message = f"Reinitialization call at {timestamp} completed."
                message += f" Time elapsed was {elapsed}.\n"
                message += f"Current version is '{revision.full_version}'."

                await self.rest.create_message(opvars.reinit_channel.id, message)

            await OperationalVariables.clear_for_reinit()
    
    async def _on_ready(self, _: hikari.ShardReadyEvent) -> None:
        """
        Handle ShardReadyEvent, completing initialization.

        Most of the stuff that happens here takes place immediately
        after forming a Discord API connection.
        """
        self.last_connection = self.localnow()
        self._permissions_root: Node = Node.build_from_client(self.lightbulb)
        await DiscordEventHandler.run_model_update(self)
        self._revision: Revision = await Revision.calculate()
        self.http_daemon = await HTTPDaemon.run(self)

        self.is_ready.set()

        await self._on_reinit()
        
        run_daemons(self)
    
    def print_banner(self, *args, **kwargs):
        """Overload banner with hakase's logo."""
        font = "ANSI Shadow"
        if font not in pyfiglet.Figlet().getFonts():
            os.system(f"python -m pyfiglet -L {os.path.join(self.conf.asset_dir, 'font/figlet/ANSI\\ Shadow.flf')}")
        f = pyfiglet.Figlet(font=font)
        lolpython.lol_py(f.renderText(self.conf.name))
        lolpython.lol_py(f"{self.conf.version.number} '{self.conf.version.tag}'")
        print("")
    
    @property
    def timezone(self) -> zoneinfo.ZoneInfo:
        """Timezone of hakase herself."""
        return zoneinfo.ZoneInfo(self.conf.timezone)

    def localnow(self) -> datetime.datetime:
        """Shortcut to get hakase's local time."""
        return utcnow().astimezone(self.timezone)

    @property
    def revision(self) -> Revision:
        """hakase's current revision."""
        if self._revision is None:
            raise RuntimeError("Current revision has not been calculated yet.")
        return self._revision

    @property
    def permissions_root(self) -> Node:
        """hakase's root permissions node."""
        if self._permissions_root is None:
            raise RuntimeError("Permissions root has not been set yet.")
        return self._permissions_root
    
    async def close(self, ctx=None, kill=False) -> None:
        """
        Restart or kill hakase.
        
        Args:
            ctx (lightbulb.Context): The context if this call is coming
                from a command.
            kill (bool): If True, hakase will not restart afterwards.


        hakase by default will restart herself when this is called. The
        external bash script checks for the presence of a file named "lock"
        in her root directory. If present, the bash script will exit the
        infinite loop it is in, resulting in a permanent shutdown.
        """
        if kill is True:
            f = await aiofile.async_open(os.path.join(self.conf.root, "lock"), "w")
            await f.close()
        else:
            if ctx:
                channel, _ = await Channel.objects.aget_or_create(id=ctx.channel_id)
                await OperationalVariables.set_for_reinit(channel=channel)

        self.logger.info("Internal ASGI webserver shutting down.")
        await self.http_daemon.shutdown()
        await super().close()
