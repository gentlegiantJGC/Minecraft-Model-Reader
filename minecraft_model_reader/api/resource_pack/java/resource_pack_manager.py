import os
import json
import copy
from typing import Union, Dict, Tuple, Iterable, Generator
from PIL import Image
import numpy
import glob

from minecraft_model_reader.api import Block
from minecraft_model_reader.api.resource_pack import BaseResourcePackManager
from minecraft_model_reader.api.resource_pack.java import java_block_model, JavaResourcePack
from minecraft_model_reader import BlockMesh

UselessImageGroups = {"colormap", "effect", "environment", "font", "gui", "map", "mob_effect", "particle"}


class JavaResourcePackManager(BaseResourcePackManager):
    """A class to load and handle the data from the packs.
    Packs are given as a list with the later packs overwriting the earlier ones."""

    def __init__(self, resource_packs: Union[JavaResourcePack, Iterable[JavaResourcePack]], load=True):
        super().__init__()
        self._blockstate_files: Dict[Tuple[str, str], dict] = {}
        self._textures: Dict[Tuple[str, str], str] = {}
        self._texture_is_transparent: Dict[str, Tuple[int, bool]] = {}
        self._model_files: Dict[Tuple[str, str], dict] = {}
        self._cached_models: Dict[Block, BlockMesh] = {}
        if isinstance(resource_packs, (list, tuple)):
            self._packs = [rp for rp in resource_packs if isinstance(rp, JavaResourcePack)]
        elif isinstance(resource_packs, JavaResourcePack):
            self._packs = [resource_packs]
        else:
            raise Exception(f'Invalid format {resource_packs}')
        if load:
            for _ in self.reload():
                pass

    def _unload(self):
        """Clear all loaded resources."""
        self._textures.clear()
        self._blockstate_files.clear()
        self._model_files.clear()
        self._cached_models.clear()

    def _load_iter(self) -> Generator[float, None, None]:
        blockstate_file_paths: Dict[Tuple[str, str], str] = {}
        model_file_paths: Dict[Tuple[str, str], str] = {}
        if os.path.isfile(os.path.join(os.path.dirname(__file__), 'transparency_cache.json')):
            try:
                with open(os.path.join(os.path.dirname(__file__), 'transparency_cache.json')) as f:
                    self._texture_is_transparent = json.load(f)
            except:
                pass

        self._textures[('minecraft', 'missing_no')] = self.missing_no

        pack_count = len(self._packs)

        for pack_index, pack in enumerate(self._packs):
            # pack_format=2 textures/blocks, textures/items - case sensitive
            # pack_format=3 textures/blocks, textures/items - lower case
            # pack_format=4 textures/block, textures/item
            # pack_format=5 model paths and texture paths are now optionally namespaced

            pack_progress = pack_index / pack_count
            yield pack_progress

            if pack.valid_pack and pack.pack_format >= 2:
                image_paths = glob.glob(
                    os.path.join(
                        glob.escape(pack.root_dir),
                        "assets",
                        "*",  # namespace
                        "textures",
                        "**",
                        "*.png"
                    ),
                    recursive=True
                )
                image_count = len(image_paths)
                sub_progress = pack_progress
                for image_index, texture_path in enumerate(image_paths):
                    _, namespace, _, *rel_path_list = os.path.normpath(os.path.relpath(texture_path, pack.root_dir)).split(os.sep)
                    if rel_path_list[0] not in UselessImageGroups:
                        rel_path = "/".join(rel_path_list)[:-4]
                        self._textures[(namespace, rel_path)] = texture_path
                        if os.stat(texture_path)[8] != self._texture_is_transparent.get(texture_path, [0])[0]:
                            im: Image.Image = Image.open(texture_path)
                            if im.mode == 'RGBA':
                                alpha = numpy.array(im.getchannel('A').getdata())
                                texture_is_transparent = numpy.any(alpha != 255)
                            else:
                                texture_is_transparent = False

                            self._texture_is_transparent[texture_path] = (os.stat(texture_path)[8], bool(texture_is_transparent))
                    yield sub_progress + image_index / (image_count * pack_count * 3)

                blockstate_paths = glob.glob(
                    os.path.join(
                        glob.escape(pack.root_dir),
                        "assets",
                        "*",  # namespace
                        "blockstates",
                        "*.json"
                    )
                )
                blockstate_count = len(blockstate_paths)
                sub_progress = pack_progress + 1 / (pack_count * 3)
                for blockstate_index, blockstate_path in enumerate(blockstate_paths):
                    _, namespace, _, blockstate_file = os.path.normpath(os.path.relpath(blockstate_path, pack.root_dir)).split(os.sep)
                    blockstate_file_paths[(namespace, blockstate_file[:-5])] = blockstate_path
                    yield sub_progress + (blockstate_index) / (blockstate_count * pack_count * 3)

                model_paths = glob.glob(
                    os.path.join(
                        glob.escape(pack.root_dir),
                        "assets",
                        "*",  # namespace
                        "models",
                        "**",
                        "*.json"
                    ),
                    recursive=True
                )
                model_count = len(model_paths)
                sub_progress = pack_progress + 2 / (pack_count * 3)
                for model_index, model_path in enumerate(model_paths):
                    _, namespace, _, *rel_path_list = os.path.normpath(os.path.relpath(model_path, pack.root_dir)).split(os.sep)
                    rel_path = "/".join(rel_path_list)[:-5]
                    model_file_paths[(namespace, rel_path.replace(os.sep, '/'))] = model_path
                    yield sub_progress + (model_index) / (model_count * pack_count * 3)

        with open(os.path.join(os.path.dirname(__file__), 'transparency_cache.json'), 'w') as f:
            json.dump(self._texture_is_transparent, f)

        for key, path in blockstate_file_paths.items():
            with open(path) as fi:
                self._blockstate_files[key] = json.load(fi)

        for key, path in model_file_paths.items():
            with open(path) as fi:
                self._model_files[key] = json.load(fi)

    @property
    def blockstate_files(self) -> Dict[Tuple[str, str], dict]:
        """Returns self._blockstate_files.
        Keys are a tuple of (namespace, relative paths used in models)
        Values are the blockstate files themselves (should be a dictionary)"""
        return self._blockstate_files

    @property
    def textures(self) -> Dict[Tuple[str, str], str]:
        """Returns a deepcopy of self._textures.
        Keys are a tuple of (namespace, relative paths used in models)
        Values are the absolute path to the texture"""
        return self._textures.copy()

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

    def texture_is_transparent(self, namespace: str, path: str) -> bool:
        return self._texture_is_transparent[self._textures[(namespace, path)]][1]

    def get_block_model(self, block: Block) -> BlockMesh:
        """Get a model for a block state.
        The block should already be in the resource pack format"""
        if block not in self._cached_models:
            self._cached_models[block] = java_block_model.get_model(self, block)
        return copy.deepcopy(self._cached_models[block])
