from ...core.conf import Config
from ..core.oauth2 import require_oauth2
from ..core.utils import template

conf = Config.load()


@template("map.html")
async def member_map(request):
    return {}
