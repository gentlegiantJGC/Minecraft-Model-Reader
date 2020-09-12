import os
import json
import copy
from typing import Union, Dict, Tuple, Iterable, Generator, List, Optional
from PIL import Image
import numpy
import glob
import itertools

import amulet_nbt

from minecraft_model_reader import log
from minecraft_model_reader.api import Block
from minecraft_model_reader.api.resource_pack import BaseResourcePackManager
from minecraft_model_reader.api.resource_pack.bedrock import BedrockResourcePack
from minecraft_model_reader.api.mesh.block.block_mesh import BlockMesh, FACE_KEYS
from minecraft_model_reader.api.mesh.util import rotate_3d
from minecraft_model_reader.api.mesh.block.cube import cull_remap_all, cube_face_lut, uv_lut, tri_face


with open(os.path.join(os.path.dirname(__file__), "blockshapes.json")) as f:
    BlockShapes = json.load(f)


class BedrockResourcePackManager(BaseResourcePackManager):
    """A class to load and handle the data from the packs.
    Packs are given as a list with the later packs overwriting the earlier ones."""

    def __init__(
        self,
        resource_packs: Union[BedrockResourcePack, Iterable[BedrockResourcePack]],
        load=True,
    ):
        super().__init__()
        self._block_shapes: Dict[str, str] = {}  # block string to block shape
        self._blocks: Dict[Tuple[str, str], Union[Dict[str, str], str, None]] = {}  # block string to short texture ids
        self._texture_data: Dict[str, List[str]] = {}  # texture ids to list of relative paths. Each relates to a different data value.
        self._textures: Dict[str, str] = {}  # relative path to texture path
        self._all_textures = None

        self._texture_is_transparent: Dict[str, Tuple[int, bool]] = {}
        self._model_files: Dict[Tuple[str, str], dict] = {}
        self._cached_models: Dict[Block, BlockMesh] = {}
        if isinstance(resource_packs, (list, tuple)):
            self._packs = [
                rp for rp in resource_packs if isinstance(rp, BedrockResourcePack)
            ]
        elif isinstance(resource_packs, BedrockResourcePack):
            self._packs = [resource_packs]
        else:
            raise Exception(f"Invalid format {resource_packs}")
        if load:
            for _ in self.reload():
                pass

    def _unload(self):
        """Clear all loaded resources."""
        self._block_shapes.clear()
        self._blocks.clear()
        self._texture_data.clear()
        self._textures.clear()
        self._all_textures = None
        self._model_files.clear()
        self._cached_models.clear()

    def _check_texture(self, texture_path: str) -> str:
        if not os.path.isfile(texture_path):
            texture_path = self.missing_no
        if (
                os.stat(texture_path)[8]
                != self._texture_is_transparent.get(texture_path, [0])[0]
        ):
            im: Image.Image = Image.open(texture_path)
            if im.mode == "RGBA":
                alpha = numpy.array(im.getchannel("A").getdata())
                texture_is_transparent = numpy.any(alpha != 255)
            else:
                texture_is_transparent = False

            self._texture_is_transparent[texture_path] = (
                os.stat(texture_path)[8],
                bool(texture_is_transparent),
            )
        return texture_path

    def _load_iter(self) -> Generator[float, None, None]:
        self._block_shapes.update(BlockShapes)  # add the default block shapes
        self._load_transparency_cache(__file__)

        self._textures["missing_no"] = self.missing_no

        pack_count = len(self._packs)

        for pack_index, pack in enumerate(self._packs):
            pack_progress = pack_index / pack_count
            yield pack_progress

            if pack.valid_pack:
                terrain_texture_path = os.path.join(pack.root_dir, "textures", "terrain_texture.json")
                if os.path.isfile(terrain_texture_path):
                    try:
                        with open(terrain_texture_path) as f:
                            terrain_texture = json.load(f)
                    except:
                        pass
                    else:
                        if isinstance(terrain_texture, dict) and "texture_data" in terrain_texture and isinstance(terrain_texture["texture_data"], dict):
                            for texture_id, data in terrain_texture["texture_data"].items():
                                if isinstance(texture_id, str) and isinstance(data, dict) and "textures" in data:
                                    texture_data = data["textures"]
                                    if isinstance(texture_data, list):
                                        self._texture_data[texture_id] = texture_data
                                        for relative_path in texture_data:
                                            self._textures[relative_path] = self._check_texture(os.path.join(pack.root_dir, relative_path))
                                    elif isinstance(texture_data, str):
                                        self._texture_data[texture_id] = [texture_data]
                                        self._textures[texture_data] = self._check_texture(os.path.join(pack.root_dir, texture_data))
                blocks_path = os.path.join(pack.root_dir, "blocks.json")
                if os.path.isfile(blocks_path):
                    try:
                        with open(blocks_path) as f:
                            blocks = json.load(f)
                    except:
                        pass
                    else:
                        if isinstance(blocks, dict):
                            for block_id, data in blocks.items():
                                if isinstance(block_id, str) and isinstance(data, dict):
                                    if ":" in block_id:
                                        namespace, base_name = block_id.split(":", 1)
                                    else:
                                        namespace = "minecraft"
                                        base_name = block_id
                                    self._blocks[(namespace, base_name)] = data.get("textures")

    @property
    def textures(self) -> Tuple[str, ...]:
        """Returns a tuple of all the texture paths in the resource pack."""
        if not self._all_textures:
            all_textures = set()
            for textures in self._textures.values():
                all_textures.update(textures)
            self._all_textures = tuple(all_textures)
        return self._all_textures

    def get_texture_path(self, namespace: Optional[str], relative_path: str) -> str:
        """Get the absolute texture path from the namespace and relative path pair"""
        if relative_path in self._textures:
            return self._textures[relative_path]
        else:
            return self.missing_no

