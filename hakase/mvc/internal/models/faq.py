from django.db import models
import jinja2
import sys

from ....core.conf import Config
from ...core.models import BaseAsyncModel


conf = Config.load()


class FAQEntry(BaseAsyncModel):
    CTX = {
        'conf': conf,
        'python_version': f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}"
    }

    title = models.CharField(max_length=256)
    text = models.TextField()

    class Meta:
        verbose_name = "FAQ Entry"
        verbose_name_plural = "FAQ Entries"

    def render(self, field):
        value = getattr(self, field)
        jinja = jinja2.Environment(loader=jinja2.BaseLoader)
        return jinja.from_string(value).render(self.ctx)

    @property
    def ctx(self):
        return FAQEntry.CTX

    def __str__(self):
        return self.render('title')