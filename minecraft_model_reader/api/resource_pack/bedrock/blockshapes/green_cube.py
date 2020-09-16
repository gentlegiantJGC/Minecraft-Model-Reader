from typing import Tuple

from minecraft_model_reader.api.mesh.block import BlockMesh
from minecraft_model_reader.api import Block
from minecraft_model_reader.api.mesh.block.cube import get_unit_cube
from minecraft_model_reader.api.resource_pack.bedrock.blockshapes.cube import Cube


class GreenCube(Cube):
    @property
    def blockshape(self) -> str:
        return "greencube"

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
        return get_unit_cube(
            down, up, north, east, south, west, int(any(transparency)), (0, 1, 0)
        )


BlockShape = GreenCube()
