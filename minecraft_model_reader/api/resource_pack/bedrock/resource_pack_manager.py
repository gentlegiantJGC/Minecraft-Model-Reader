import os
import json
from typing import Union, Dict, Tuple, Iterable, Generator, Optional
from PIL import Image
import numpy

from minecraft_model_reader.api import Block, comment_json
from minecraft_model_reader.api.resource_pack import BaseResourcePackManager
from minecraft_model_reader.api.resource_pack.bedrock import BedrockResourcePack
from minecraft_model_reader.api.mesh.block.block_mesh import BlockMesh
from .blockshapes import BlockShapeClasses


def _load_data() -> Tuple[
    Dict[str, str],
    Dict[
        str, Tuple[Tuple[Tuple[str, str], ...], Dict[Tuple[Union[str, int], ...], int]]
    ],
]:
    with open(os.path.join(os.path.dirname(__file__), "blockshapes.json")) as f:
        _block_shapes = comment_json.load(f)

    _aux_values = {}
    with open(os.path.join(os.path.dirname(__file__), "block_palette.json")) as f:
        _block_palette = comment_json.load(f)
    for block in _block_palette["blocks"]:
        data = block["data"]
        name = block["name"]
        if name not in _aux_values:
            _aux_values[name] = (
                tuple((state["name"], state["value"]) for state in block["states"]),
                {},
            )
        _aux_values[name][1][tuple(state["value"] for state in block["states"])] = data

    return _block_shapes, _aux_values


BlockShapes, AuxValues = _load_data()


def get_aux_value(block: Block) -> int:
    name = block.namespaced_name
    if name in AuxValues:
        property_names, aux_map = AuxValues[name]
        properties = block.properties
        key = tuple(
            properties[property_name].py_data if property_name in properties else default
            for property_name, default in property_names
        )
        return aux_map.get(key, 0)
    else:
        return 0


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
        self._blocks: Dict[
            str, Union[Dict[str, str], str, None]
        ] = {}  # block string to short texture ids
        self._terrain_texture: Dict[
            str, Tuple[str, ...]
        ] = (
            {}
        )  # texture ids to list of relative paths. Each relates to a different data value.
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

        self._textures["missing_no"] = self._check_texture("missing")

        pack_count = len(self._packs)

        for pack_index, pack in enumerate(self._packs):
            pack_progress = pack_index / pack_count
            yield pack_progress

            if pack.valid_pack:
                terrain_texture_path = os.path.join(
                    pack.root_dir, "textures", "terrain_texture.json"
                )
                if os.path.isfile(terrain_texture_path):
                    try:
                        with open(terrain_texture_path) as f:
                            terrain_texture = comment_json.load(f)
                    except json.JSONDecodeError:
                        pass
                    else:
                        if (
                            isinstance(terrain_texture, dict)
                            and "texture_data" in terrain_texture
                            and isinstance(terrain_texture["texture_data"], dict)
                        ):
                            sub_progress = pack_progress
                            image_count = len(terrain_texture["texture_data"])

                            def get_texture(_relative_path):
                                if isinstance(_relative_path, dict):
                                    _relative_path = _relative_path.get(
                                        "path", "misssingno"
                                    )
                                if isinstance(_relative_path, str):
                                    full_path = self._check_texture(
                                        os.path.join(pack.root_dir, _relative_path)
                                    )
                                    if _relative_path in self._textures:
                                        if full_path != self.missing_no:
                                            self._textures[_relative_path] = full_path
                                    else:
                                        self._textures[_relative_path] = full_path
                                return _relative_path

                            for image_index, (texture_id, data) in enumerate(
                                terrain_texture["texture_data"].items()
                            ):
                                if (
                                    isinstance(texture_id, str)
                                    and isinstance(data, dict)
                                    and "textures" in data
                                ):
                                    texture_data = data["textures"]
                                    if isinstance(texture_data, list):
                                        self._terrain_texture[texture_id] = tuple(
                                            get_texture(relative_path)
                                            for relative_path in texture_data
                                        )
                                    else:
                                        self._terrain_texture[texture_id] = (
                                            get_texture(texture_data),
                                        ) * 16
                                yield sub_progress + image_index / (
                                    image_count * pack_count * 2
                                )
                sub_progress = pack_progress + 1 / (pack_count * 2)
                yield sub_progress
                blocks_path = os.path.join(pack.root_dir, "blocks.json")
                if os.path.isfile(blocks_path):
                    try:
                        with open(blocks_path) as f:
                            blocks = comment_json.load(f)
                    except json.JSONDecodeError:
                        pass
                    else:
                        if isinstance(blocks, dict):
                            model_count = len(blocks)
                            for model_index, (block_id, data) in enumerate(
                                blocks.items()
                            ):
                                if isinstance(block_id, str) and isinstance(data, dict):
                                    if ":" not in block_id:
                                        block_id = "minecraft:" + block_id
                                    self._blocks[block_id] = data.get("textures")
                                yield sub_progress + (model_index) / (
                                    model_count * pack_count * 2
                                )
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

        if block_shape in BlockShapeClasses:
            block_shape_class = BlockShapeClasses[block_shape]
        else:
            block_shape_class = BlockShapeClasses["cube"]

        if not block_shape_class.is_valid(block):
            block_shape_class = BlockShapeClasses["cube"]

        texture_index = block_shape_class.texture_index(block, get_aux_value(block))

        if block.namespaced_name in self._blocks:
            texture_id = self._blocks[block.namespaced_name]
            if isinstance(texture_id, str):
                up = down = north = east = south = west = self._get_texture(
                    texture_id, texture_index
                )
                transparent = (self._texture_is_transparent[up][1],) * 6

            elif isinstance(texture_id, dict):
                down = self._get_texture(
                    texture_id.get("down", "missing"), texture_index
                )
                up = self._get_texture(texture_id.get("up", "missing"), texture_index)

                if "side" in texture_id:
                    north = east = south = west = self._get_texture(
                        texture_id.get("side", "missing"), texture_index
                    )
                    transparent = (
                        self._texture_is_transparent[down][1],
                        self._texture_is_transparent[up][1],
                    ) + (self._texture_is_transparent[north][1],) * 4
                else:
                    north = self._get_texture(
                        texture_id.get("north", "missing"), texture_index
                    )
                    east = self._get_texture(
                        texture_id.get("east", "missing"), texture_index
                    )
                    south = self._get_texture(
                        texture_id.get("south", "missing"), texture_index
                    )
                    west = self._get_texture(
                        texture_id.get("west", "missing"), texture_index
                    )
                    transparent = (
                        self._texture_is_transparent[down][1],
                        self._texture_is_transparent[up][1],
                        self._texture_is_transparent[north][1],
                        self._texture_is_transparent[east][1],
                        self._texture_is_transparent[south][1],
                        self._texture_is_transparent[west][1],
                    )
            else:
                up = down = north = east = south = west = self._get_texture(
                    "missing", texture_index
                )
                transparent = (self._texture_is_transparent[up][1],) * 6

            return block_shape_class.get_block_model(
                block, down, up, north, east, south, west, transparent
            )

        return self.missing_block

    def _get_texture(self, texture_id: str, index: int):
        texture = self.missing_no
        if texture_id in self._terrain_texture:
            texture_list = self._terrain_texture[texture_id]
            if len(texture_list) > index:
                texture = self.get_texture_path(None, texture_list[index])
        return texture
