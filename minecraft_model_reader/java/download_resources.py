import os
import shutil
import zipfile
import json
from urllib.request import urlopen
import io

from . import launcher_manifest
import minecraft_model_reader
from minecraft_model_reader import log
from .java_rp_handler import JavaRP


def get_latest() -> JavaRP:
    vanilla_rp_path = os.path.join(minecraft_model_reader.path, 'resource_packs', 'java_vanilla')
    new_version = launcher_manifest['latest']['release']
    if new_version is None:
        if os.path.isdir(vanilla_rp_path):
            log.error('Could not download the launcher manifest. The resource pack seems to be present so using that.')
        else:
            log.error('Could not download the launcher manifest. The resource pack is not present, blocks may not be rendered correctly.')
    else:
        if os.path.isdir(vanilla_rp_path):
            if os.path.isfile(os.path.join(vanilla_rp_path, 'version')):
                with open(os.path.join(vanilla_rp_path, 'version')) as f:
                    old_version = f.read()
                if old_version != new_version:
                    _remove_and_download(vanilla_rp_path, new_version)
            else:
                _remove_and_download(vanilla_rp_path, new_version)
        else:
            _remove_and_download(vanilla_rp_path, new_version)
    return JavaRP(vanilla_rp_path)


def _remove_and_download(path, version):
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    if download_resources(path, version):
        with open(os.path.join(path, 'version'), 'w') as f:
            f.write(version)


def download_resources(path, version) -> bool:
    log.info(f'Downloading Java resource pack for version {version}')
    version_url = next((v["url"] for v in launcher_manifest['versions'] if v['id'] == version), None)
    if version_url is None:
        log.error(f'Could not find Java resource pack for version {version}.')
        return False

    try:
        version_manifest = json.load(urlopen(version_url))
        version_client_url = version_manifest["downloads"]["client"]["url"]

        client = zipfile.ZipFile(io.BytesIO(urlopen(version_client_url).read()))
        for fpath in client.namelist():
            if fpath.startswith('assets/'):
                client.extract(fpath, path)
        client.extract('pack.mcmeta', path)
        client.extract('pack.png', path)

    except:
        log.error(
            f'Failed to download and extract the Java resource pack for version {version}. Make sure you have a connection to the internet.',
            exc_info=True
        )
        return False
    return True
