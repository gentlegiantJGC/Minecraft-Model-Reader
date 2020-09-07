from .base_resource_pack import BaseResourcePack


class UnknownResourcePack(BaseResourcePack):
    def __repr__(self):
        return f'UnknownResourcePack({self._root_dir})'
