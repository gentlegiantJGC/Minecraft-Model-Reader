from typing import List, Dict, Tuple, Generator, Optional
import os
import json
import copy

from minecraft_model_reader.api import Block, BlockMesh
from minecraft_model_reader.api.resource_pack.base.resource_pack import BaseResourcePack
from minecraft_model_reader.api.image import missing_no_path
from minecraft_model_reader.api.mesh.block.missing_block import get_missing_block


class BaseResourcePackManager:
    """The base class that all resource pack managers must inherit from. Defines the base api."""

    def __init__(self):
        self._packs: List[BaseResourcePack] = []
        self._missing_block = None
        self._texture_is_transparent = {}
        self._cached_models: Dict[Block, BlockMesh] = {}

    @property
    def pack_paths(self):
        return [pack.root_dir for pack in self._packs]

    def _unload(self):
        """Clear all loaded resources."""
        self._texture_is_transparent.clear()
        self._cached_models.clear()

    def _load_transparency_cache(self, path: str):
        if os.path.isfile(
            os.path.join(os.path.dirname(path), "transparency_cache.json")
        ):
            try:
                with open(
                    os.path.join(os.path.dirname(path), "transparency_cache.json")
                ) as f:
                    self._texture_is_transparent = json.load(f)
            except:
                pass

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

    @property
    def missing_block(self) -> BlockMesh:
        if self._missing_block is None:
            self._missing_block = get_missing_block(self)
        return self._missing_block

    @property
    def textures(self) -> Tuple[str, ...]:
        """Returns a tuple of all the texture paths in the resource pack."""
        raise NotImplementedError

    def get_texture_path(self, namespace: Optional[str], relative_path: str) -> str:
        """Get the absolute texture path from the namespace and relative path pair"""
        raise NotImplementedError

    def get_block_model(self, block: Block) -> BlockMesh:
        """Get a model for a block state.
        The block should already be in the resource pack format"""
        if block not in self._cached_models:
            if block.extra_blocks:
                self._cached_models[block] = BlockMesh.merge(
                    (self._get_model(block.base_block),)
                    + tuple(self._get_model(block_) for block_ in block.extra_blocks)
                )
            else:
                self._cached_models[block] = self._get_model(block)
        return copy.deepcopy(self._cached_models[block])

    def _get_model(self, block: Block) -> BlockMesh:
        raise NotImplementedError
