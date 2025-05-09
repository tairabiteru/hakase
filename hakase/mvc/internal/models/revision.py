import aiofile
import colorlog
from django.db import models
import hashlib
import os

from ....core.conf import Config, __VERSION__, __TAG__
from ...core.models import BaseAsyncModel


conf = Config.load()
logger = colorlog.getLogger(conf.name)


class Revision(BaseAsyncModel):
    CODE_EXTENSIONS = [
        ".py", ".html", ".js", ".css"
    ]

    EXCLUDE_FOLDERS = [
        ".venv", "migrations", "logs", "static/admin", "bin"
    ]

    hash = models.CharField(max_length=128, help_text="The SHA512 digest of the codebase.")
    lines = models.IntegerField(help_text="The number of code lines in the codebase.")
    chars = models.IntegerField(help_text="The number of code characters in the codebase.")
    files = models.IntegerField(help_text="The number of code files in the codebase.")
    size = models.IntegerField(help_text="The total size in bytes of the entire root directory.")
    number = models.IntegerField(help_text="The revision number.")
    version = models.CharField(max_length=64, help_text="The name of the major version.")
    tag = models.CharField(max_length=128, help_text="The version tag, appearing after the major version and revision number.")
    timestamp = models.DateTimeField(auto_now_add=True, help_text="The time when this version was first entered into.")

    class Meta:
        get_latest_by = "timestamp"
    
    def __eq__(self, other):
        fields = ['version', 'lines', 'hash']
        for field in fields:
            if getattr(self, field) != getattr(other, field):
                return False
        else:
            return True
    
    def __str__(self):
        return f"{conf.name} {self.full_version}"

    @property
    def full_version(self):
        return f"{self.version} R.{self.number} '{self.tag}'"
    
    @classmethod
    async def recompute_current(cls):
        lines = 0
        chars = 0
        files = 0
        size = 0
        hash = hashlib.sha512()

        for subdir, dirs, fs in os.walk(os.path.join(conf.root)):
            if not any([f in subdir for f in cls.EXCLUDE_FOLDERS]):
                for file in fs:
                    files += 1
                    size += os.path.getsize(os.path.join(subdir, file))

                    if any([file.endswith(ext) for ext in cls.CODE_EXTENSIONS]):
                        async with aiofile.async_open(os.path.join(subdir, file), "rb") as fh:
                            data = await fh.read()
                            hash.update(data)
                            chars += len(data)
                            data = list(reversed(data.split(b"\n")))
                            for i, line in enumerate(data):
                                if line == b"":
                                    data.pop(i)
                                else:
                                    break
                            lines += len(data)
        
        hash = hash.hexdigest()

        try:
            last = await cls.objects.alatest()
            if last.version != __VERSION__:
                number = 0
            else:
                number = last.number + 1
        except cls.DoesNotExist:
            number = 0
        
        current = cls(
            hash=hash,
            lines=lines,
            chars=chars,
            files=files,
            size=size,
            number=number,
            version=__VERSION__,
            tag=__TAG__
        )
        return current
    
    @classmethod
    async def calculate(cls):
        try:
            last = await cls.objects.alatest()
        except cls.DoesNotExist:
            logger.warning("No existing revisions in database. Recomputing.")
            current = await cls.recompute_current()
            await current.asave()
            return current
        
        apparent = await cls.recompute_current()
        if last != apparent:
            if last.version != apparent.version:
                logger.warning(f"Major version is different: {last.version} =/= {apparent.version}.")
            elif last.lines != apparent.lines:
                verb = "added" if apparent.lines > last.lines else "removed"
                prepos = "to" if apparent.lines > last.lines else "from"
                plural = "line" if abs(apparent.lines - last.lines) == 1 else "lines"
                logger.warning(f"{abs(apparent.lines - last.lines)} {plural} {verb} {prepos} codebase.")
            elif last.hash != apparent.hash:
                logger.warning(f"Current hash {apparent.hash[-8:]} =/= last hash {last.hash[-8:]}.")
            await apparent.asave()
            return apparent
        else:
            logger.info("No changes detected in codebase.")
            return last