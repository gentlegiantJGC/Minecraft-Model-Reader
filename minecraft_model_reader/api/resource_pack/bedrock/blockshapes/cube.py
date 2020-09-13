from typing import Tuple

from minecraft_model_reader.api.mesh.block import BlockMesh
from minecraft_model_reader.api import Block
from minecraft_model_reader.api.mesh.block.cube import get_unit_cube
from minecraft_model_reader.api.resource_pack.bedrock.blockshapes.base_blockshape import BaseBlockShape


class Cube(BaseBlockShape):
    @property
    def blockshape(self) -> str:
        return "cube"

    def is_valid(self, block: Block) -> bool:
        """Does the given block have the correct properties to use this blockshape"""
        return True

    def texture_index(self, aux_value: int) -> int:
        """The texture index to use within the list for the given Block"""
        return aux_value % 16

    def get_block_model(self, block: Block, down: str, up: str, north: str, east: str, south: str, west: str, transparency: Tuple[int, int, int, int, int, int]) -> BlockMesh:
        return get_unit_cube(
            down,
            up,
            north,
            east,
            south,
            west,
            int(any(transparency))
        )


BlockShape = Cube()
