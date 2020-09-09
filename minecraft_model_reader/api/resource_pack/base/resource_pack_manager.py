from typing import List, Dict, Tuple, Generator

from minecraft_model_reader.api import Block, BlockMesh
from minecraft_model_reader.api.resource_pack.base.resource_pack import BaseResourcePack
from minecraft_model_reader.api.image import missing_no_path


class BaseResourcePackManager:
    """The base class that all resource pack managers must inherit from. Defines the base api."""

    def __init__(self):
        self._packs: List[BaseResourcePack] = []

    @property
    def pack_paths(self):
        return [pack.root_dir for pack in self._packs]

    def _unload(self):
        """Clear all loaded resources."""
        raise NotImplementedError

    def _load_iter(self) -> Generator[float, None, None]:
        """Load resources."""
        raise NotImplementedError

    def reload(self) -> Generator[float, None, None]:
        """Unload and reload resources"""
        self._unload()
        yield from self._load_iter()

    @property
    def missing_no(self) -> str:
        """The path to the missing_no image"""
        return missing_no_path

    def get_block_model(self, block: Block) -> BlockMesh:
        raise NotImplemented
