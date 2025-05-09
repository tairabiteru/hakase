from ...core.conf import Config
from ..core.utils import template
from ..core.oauth2 import require_oauth2
from .models import ServiceModel


conf = Config.load()


@require_oauth2()
@template("services.html")
async def services(request):
    ctx = {'services': [], 'bot_name': conf.name}
    async for service in ServiceModel.objects.all():
        ctx['services'].append(service)
    return ctx


