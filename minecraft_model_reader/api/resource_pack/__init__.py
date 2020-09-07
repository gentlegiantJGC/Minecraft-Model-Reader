from .java_resource_pack import JavaResourcePack
from .unknown_resource_pack import UnknownResourcePack


def load(resource_pack_path: str):
    if JavaResourcePack.is_valid(resource_pack_path):
        return JavaResourcePack(resource_pack_path)
    else:
        return UnknownResourcePack(resource_pack_path)
