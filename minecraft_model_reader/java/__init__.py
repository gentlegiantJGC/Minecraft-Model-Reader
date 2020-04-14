import json
from urllib.request import urlopen
from minecraft_model_reader import log

try:
    launcher_manifest = json.load(urlopen('https://launchermeta.mojang.com/mc/game/version_manifest.json', timeout=0.3))
except:
    log.error('Failed to download the launcher manifest. This may cause problems if you have not used the program before. Make sure you are connected to the internet.')
    launcher_manifest = {
        "latest": {
            "release": None
        }
    }
