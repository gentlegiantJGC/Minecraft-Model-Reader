from .base_resource_pack import BaseResourcePack


class UnknownResourcePack(BaseResourcePack):
    def __repr__(self):
        return f'UnknownResourcePack({self._root_dir})'

    @staticmethod
    def is_valid(pack_path: str):
        return True
