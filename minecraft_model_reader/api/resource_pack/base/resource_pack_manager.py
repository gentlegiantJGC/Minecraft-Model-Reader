from typing import List, Dict, Tuple

from minecraft_model_reader.api import Block, BlockMesh
from minecraft_model_reader.api.resource_pack.base.resource_pack import BaseResourcePack
from minecraft_model_reader.api.image import missing_no_path


class BaseResourcePackManager:
    """The base class that all resource pack handlers must inherit from. Defines the base api."""

    def __init__(self):
        self._packs: List[BaseResourcePack] = []
        self._missing_no = missing_no_path
        self._textures: Dict[Tuple[str, str], str] = {}
        self._texture_is_transparent: Dict[str, List[int, bool]] = {}
        self._blockstate_files: Dict[Tuple[str, str], dict] = {}
        self._model_files: Dict[Tuple[str, str], dict] = {}
        self._cached_models: Dict[Block, BlockMesh] = {}

    @property
    def pack_paths(self):
        return [pack.root_dir for pack in self._packs]

    def unload(self):
        """Clear all loaded resources."""
        self._textures.clear()
        self._blockstate_files.clear()
        self._model_files.clear()
        self._cached_models.clear()

    @property
    def missing_no(self) -> str:
        """The path to the missing_no image"""
        return self._missing_no

    @property
    def textures(self) -> Dict[Tuple[str, str], str]:
        """Returns a deepcopy of self._textures.
        Keys are a tuple of (namespace, relative paths used in models)
        Values are the absolute path to the texture"""
        return self._textures.copy()

    @property
    def blockstate_files(self) -> Dict[Tuple[str, str], dict]:
        """Returns self._blockstate_files.
        Keys are a tuple of (namespace, relative paths used in models)
        Values are the blockstate files themselves (should be a dictionary)"""
        return self._blockstate_files

    @property
    def model_files(self) -> Dict[Tuple[str, str], dict]:
        """Returns self._model_files.
        Keys are a tuple of (namespace, relative paths used in models)
        Values are the model files themselves (should be a dictionary or BlockMesh)"""
        return self._model_files

    def get_texture(self, namespace_and_path: Tuple[str, str]) -> str:
        """Get the absolute texture path from the namespace and relative path pair"""
        if namespace_and_path in self._textures:
            return self._textures[namespace_and_path]
        else:
            return self._missing_no

    def get_model(self, block: 'Block'):
        raise NotImplemented
