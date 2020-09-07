from typing import Iterable, Union

from minecraft_model_reader.api.resource_pack.base import BaseResourcePack, BaseResourcePackManager
from minecraft_model_reader.api.resource_pack.java import JavaResourcePack, JavaResourcePackManager
from .unknown_resource_pack import UnknownResourcePack


def load_resource_pack(resource_pack_path: str):
    if JavaResourcePack.is_valid(resource_pack_path):
        return JavaResourcePack(resource_pack_path)
    else:
        return UnknownResourcePack(resource_pack_path)


def load_resource_pack_manager(resource_packs: Iterable[Union[str, BaseResourcePack]]) -> BaseResourcePackManager:
    resource_packs = [resource_pack if isinstance(resource_pack, BaseResourcePack) else load_resource_pack(resource_pack) for resource_pack in resource_packs]
