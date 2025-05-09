import orjson as json
import os
import subprocess

from ..core.conf import Config


conf = Config.load()


async def lint_lib():

    process = subprocess.run(
        ["ruff", "check", os.path.join(conf.root_dir, "hakase"), "--output-format=json"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        encoding="utf-8"
    )
    data = json.loads(process.stdout)
    for i, info in enumerate(data):
        info['filename'] = info['filename'].replace(os.path.join(conf.root_dir, "hakase/"), "")
        data[i] = info
    return data

