from typing import Tuple
import numpy

from minecraft_model_reader.api.mesh.block import BlockMesh
from minecraft_model_reader.api import Block
from minecraft_model_reader.api.resource_pack.bedrock.blockshapes.cube import Cube


class RedDust(Cube):
    @property
    def blockshape(self) -> str:
        return "red_dust"

    def get_block_model(self, block: Block, down: str, up: str, north: str, east: str, south: str, west: str, transparency: Tuple[bool, bool, bool, bool, bool, bool]) -> BlockMesh:
        return BlockMesh(
            3,
            {None: numpy.array([0.0, 0.0625, 1.0, 1.0, 0.0625, 1.0, 1.0, 0.0625, 0.0, 0.0, 0.0625, 0.0], dtype=numpy.float32)},
            {None: numpy.array([0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0], numpy.float32)},
            {None: numpy.array([1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0], numpy.float32)},
            {None: numpy.array([0, 1, 2, 0, 2, 3], numpy.uint32)},
            {None: numpy.array([0, 0], numpy.uint32)},
            (up,),
            int(transparency[1])
        )


BlockShape = RedDust()
