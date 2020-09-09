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
    resource_packs_out = []
    for resource_pack in resource_packs:
        if isinstance(resource_pack, str):
            resource_pack = load_resource_pack(resource_pack)
        if not isinstance(resource_pack, UnknownResourcePack) and resource_pack.valid_pack:
            if resource_packs_out:
                if isinstance(resource_pack, resource_packs_out[0].__class__):
                    resource_packs_out.append(resource_pack)
            else:
                resource_packs_out.append(resource_pack)

    resource_packs = resource_packs_out
    if resource_packs:
        if isinstance(resource_packs[0], JavaResourcePack):
            return JavaResourcePackManager(resource_packs)

    raise NotImplementedError
    # return UnknownResourcePackManager()