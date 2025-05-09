from asgiref.sync import sync_to_async

from ...core.conf import Config
from .utils import template


conf = Config.load()


@template("index.html")
async def index(request):
    authenticated = await sync_to_async(lambda: request.user.is_authenticated)()
    uid = request.session.get("uid", None)
    return {
        'avatar_url': request.bot.get_me().avatar_url,
        'name': request.bot.get_me().username,
        'version': f"v{request.bot.conf.version.number} '{request.bot.conf.version.tag}'",
        'display_admin': authenticated or uid == conf.owner_id
    }