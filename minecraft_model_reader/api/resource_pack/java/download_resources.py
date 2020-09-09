import os
import shutil
import zipfile
import json
from urllib.request import urlopen
import io
from typing import Generator

import minecraft_model_reader
from minecraft_model_reader import log
from minecraft_model_reader.api.resource_pack import JavaResourcePack

RESOURCE_PACK_DIR = os.path.join(
    minecraft_model_reader.path, "api", "resource_pack", "java", "resource_packs"
)

try:
    log.info("Downloading java launcher manifest file.")
    launcher_manifest = json.load(
        urlopen("https://launchermeta.mojang.com/mc/game/version_manifest.json")
    )
except Exception as e:
    log.error(
        f'Failed to download the launcher manifest. "{e}" This may cause problems if you have not used the program before. Make sure you are connected to the internet and https://mojang.com is not blocked.'
    )
    launcher_manifest = {"latest": {"release": None}}


def generator_unpacker(gen: Generator):
    try:
        while True:
            next(gen)
    except StopIteration as e:
        return e.value


def get_latest() -> JavaResourcePack:
    return generator_unpacker(get_latest_iter())


def get_latest_iter() -> Generator[float, None, JavaResourcePack]:
    vanilla_rp_path = os.path.join(RESOURCE_PACK_DIR, "java_vanilla")
    new_version = launcher_manifest["latest"]["release"]
    if new_version is None:
        if os.path.isdir(vanilla_rp_path):
            log.error(
                "Could not download the launcher manifest. The resource pack seems to be present so using that."
            )
        else:
            log.error(
                "Could not download the launcher manifest. The resource pack is not present, blocks may not be rendered correctly."
            )
    else:
        if os.path.isdir(vanilla_rp_path):
            if os.path.isfile(os.path.join(vanilla_rp_path, "version")):
                with open(os.path.join(vanilla_rp_path, "version")) as f:
                    old_version = f.read()
                if old_version != new_version:
                    yield from _remove_and_download_iter(vanilla_rp_path, new_version)
            else:
                yield from _remove_and_download_iter(vanilla_rp_path, new_version)
        else:
            yield from _remove_and_download_iter(vanilla_rp_path, new_version)
    return JavaResourcePack(vanilla_rp_path)


_java_vanilla_fix = None
_java_vanilla_latest = None


def get_java_vanilla_fix():
    global _java_vanilla_fix
    if _java_vanilla_fix is None:
        _java_vanilla_fix = JavaResourcePack(
            os.path.join(RESOURCE_PACK_DIR, "java_vanilla_fix")
        )
    return _java_vanilla_fix


def get_java_vanilla_latest():
    global _java_vanilla_latest
    if _java_vanilla_latest is None:
        _java_vanilla_latest = get_latest()
    return _java_vanilla_latest


def get_java_vanilla_latest_iter() -> Generator[float, None, JavaResourcePack]:
    global _java_vanilla_latest
    if _java_vanilla_latest is None:
        _java_vanilla_latest = yield from get_latest_iter()
    return _java_vanilla_latest


def _remove_and_download(path, version):
    for _ in _remove_and_download_iter(path, version):
        pass


def _remove_and_download_iter(path, version) -> Generator[float, None, None]:
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    exists = yield from download_resources_iter(path, version)
    if exists:
        with open(os.path.join(path, "version"), "w") as f:
            f.write(version)


def download_resources(path, version) -> bool:
    return generator_unpacker(download_resources_iter(path, version))


def download_resources_iter(
    path, version, chunk_size=4096
) -> Generator[float, None, bool]:
    log.info(f"Downloading Java resource pack for version {version}")
    version_url = next(
        (v["url"] for v in launcher_manifest["versions"] if v["id"] == version), None
    )
    if version_url is None:
        log.error(f"Could not find Java resource pack for version {version}.")
        return False

    try:
        version_manifest = json.load(urlopen(version_url))
        version_client_url = version_manifest["downloads"]["client"]["url"]

        response = urlopen(version_client_url)
        data = []
        data_size = int(response.headers["content-length"].strip())
        index = 0
        chunk = b"hello"
        while chunk:
            chunk = response.read(chunk_size)
            data.append(chunk)
            index += 1
            yield min(1.0, (index * chunk_size) / (data_size * 2))

        client = zipfile.ZipFile(io.BytesIO(b"".join(data)))
        paths = [fpath for fpath in client.namelist() if fpath.startswith("assets/")]
        path_count = len(paths)
        for path_index, fpath in enumerate(paths):
            if not path_index % 30:
                yield path_index / (path_count * 2) + 0.5
            client.extract(fpath, path)
        client.extract("pack.mcmeta", path)
        client.extract("pack.png", path)

    except:
        log.error(
            f"Failed to download and extract the Java resource pack for version {version}. Make sure you have a connection to the internet.",
            exc_info=True,
        )
        return False
    log.info(f"Finished downloading Java resource pack for version {version}")
    return True
