from typing import Tuple

from minecraft_model_reader.api.resource_pack.bedrock.blockshapes.partial_block import (
    PartialBlock,
)
from minecraft_model_reader.api import Block
from minecraft_model_reader.api.mesh.block import BlockMesh
import amulet_nbt


class Repeater(PartialBlock):
    def is_valid(self, block: Block) -> bool:
        return isinstance(block.properties.get("direction"), amulet_nbt.TAG_Int)

    @property
    def blockshape(self) -> str:
        return "repeater"

    def texture_index(self, block: Block, aux_value: int) -> int:
        if block.base_name == "powered_repeater":
            return 1
        else:
            return 0

    def bounds(
        self, block: Block
    ) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        return (0, 1), (0, 2 / 16), (0, 1)

    @property
    def do_not_cull(self) -> Tuple[bool, bool, bool, bool, bool, bool]:
        return False, True, False, False, False, False

    def get_block_model(
        self,
        block: Block,
        down: str,
        up: str,
        north: str,
        east: str,
        south: str,
        west: str,
        transparency: Tuple[bool, bool, bool, bool, bool, bool],
    ) -> BlockMesh:
        return (
            super()
            .get_block_model(block, down, up, north, east, south, west, transparency)
            .rotate(0, block.properties["direction"].value)
        )


BlockShape = Repeater()
