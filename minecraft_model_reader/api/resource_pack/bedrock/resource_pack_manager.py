import os
import json
from typing import Union, Dict, Tuple, Iterable, Generator, List, Optional
from PIL import Image
import numpy

from minecraft_model_reader import log
from minecraft_model_reader.api import Block
from minecraft_model_reader.api.resource_pack import BaseResourcePackManager
from minecraft_model_reader.api.resource_pack.bedrock import BedrockResourcePack
from minecraft_model_reader.api.mesh.block.block_mesh import BlockMesh, FACE_KEYS
from minecraft_model_reader.api.mesh.util import rotate_3d
from minecraft_model_reader.api.mesh.block.cube import cull_remap_all, cube_face_lut, uv_rotation_lut, tri_face, get_unit_cube

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
        self._blocks: Dict[str, Union[Dict[str, str], str, None]] = {}  # block string to short texture ids
        self._terrain_texture: Dict[str, List[str]] = {}  # texture ids to list of relative paths. Each relates to a different data value.
        self._textures: Dict[str, str] = {}  # relative path to texture path
        self._all_textures = None

        self._texture_is_transparent: Dict[str, Tuple[int, bool]] = {}

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
        super()._unload()
        self._block_shapes.clear()
        self._blocks.clear()
        self._terrain_texture.clear()
        self._textures.clear()
        self._all_textures = None

    def _check_texture(self, texture_path: str) -> str:
        if os.path.isfile(texture_path + ".png"):
            texture_path += ".png"
        elif os.path.isfile(texture_path + ".tga"):
            texture_path += ".tga"
        else:
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
                            sub_progress = pack_progress
                            image_count = len(terrain_texture["texture_data"])

                            def get_texture(_relative_path):
                                if isinstance(_relative_path, dict):
                                    _relative_path = _relative_path.get("path", "misssingno")
                                if isinstance(_relative_path, str):
                                    self._textures[_relative_path] = self._check_texture(os.path.join(pack.root_dir, _relative_path))
                                return _relative_path

                            for image_index, (texture_id, data) in enumerate(terrain_texture["texture_data"].items()):
                                if isinstance(texture_id, str) and isinstance(data, dict) and "textures" in data:
                                    texture_data = data["textures"]
                                    if isinstance(texture_data, list):
                                        self._terrain_texture[texture_id] = [get_texture(relative_path) for relative_path in texture_data]
                                    else:
                                        self._terrain_texture[texture_id] = [get_texture(texture_data)]
                                yield sub_progress + image_index / (image_count * pack_count * 2)
                sub_progress = pack_progress + 1 / (pack_count * 2)
                yield sub_progress
                blocks_path = os.path.join(pack.root_dir, "blocks.json")
                if os.path.isfile(blocks_path):
                    try:
                        with open(blocks_path) as f:
                            blocks = json.load(f)
                    except:
                        pass
                    else:
                        if isinstance(blocks, dict):
                            model_count = len(blocks)
                            for model_index, (block_id, data) in enumerate(blocks.items()):
                                if isinstance(block_id, str) and isinstance(data, dict):
                                    if ":" not in block_id:
                                        block_id = "minecraft:" + block_id
                                    self._blocks[block_id] = data.get("textures")
                                yield sub_progress + (model_index) / (model_count * pack_count * 2)
            yield pack_progress + 1

        with open(
                os.path.join(os.path.dirname(__file__), "transparency_cache.json"), "w"
        ) as f:
            json.dump(self._texture_is_transparent, f)

    @property
    def textures(self) -> Tuple[str, ...]:
        """Returns a tuple of all the texture paths in the resource pack."""
        return tuple(self._textures.values())

    def get_texture_path(self, namespace: Optional[str], relative_path: str) -> str:
        """Get the absolute texture path from the namespace and relative path pair"""
        if relative_path in self._textures:
            return self._textures[relative_path]
        else:
            return self.missing_no

    def _get_model(self, block: Block) -> BlockMesh:
        block_shape = self._block_shapes.get(block.namespaced_name, "cube")
        if block_shape == "invisible":
            return BlockMesh(
                3,
                {},
                {},
                {},
                {},
                {},
                (),
                2
            )
        # if block_shape == "cube":
        #
        # else:
        #     return self.missing_block

        if block.namespaced_name in self._blocks:
            texture_id = self._blocks[block.namespaced_name]
            if isinstance(texture_id, str):
                texture = self._get_texture(texture_id)
                return get_unit_cube(
                    texture,
                    texture,
                    texture,
                    texture,
                    texture,
                    texture,
                    int(self._texture_is_transparent[texture][1])
                )
            elif isinstance(texture_id, dict):
                texture_keys = texture_id.keys()
                if texture_keys == {'down', 'side', 'up'}:
                    down = self._get_texture(texture_id["down"])
                    up = self._get_texture(texture_id["up"])
                    side = self._get_texture(texture_id["side"])
                    return get_unit_cube(
                        down,
                        up,
                        side,
                        side,
                        side,
                        side,
                        int(any(self._texture_is_transparent[t][1] for t in (down, up, side)))
                    )
                elif texture_keys == {'down', 'east', 'north', 'south', 'up', 'west'}:
                    textures = [self._get_texture(texture_id[face]) for face in (
                        "down",
                        "up",
                        "north",
                        "east",
                        "south",
                        "west",
                    )]
                    return get_unit_cube(*textures, int(any(self._texture_is_transparent[t][1] for t in textures)))

        return self.missing_block

    def _get_texture(self, texture_id: str):
        texture = self.missing_no
        if texture_id in self._terrain_texture:
            texture_list = self._terrain_texture[texture_id]
            if texture_list:
                texture = self.get_texture_path(None, texture_list[0])  # TODO: add support for the other data values
        return texture
