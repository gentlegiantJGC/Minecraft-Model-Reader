from typing import Tuple

from minecraft_model_reader.api.mesh.block import BlockMesh
from minecraft_model_reader.api import Block
from minecraft_model_reader.api.mesh.block.cube import get_cube
from minecraft_model_reader.api.resource_pack.bedrock.blockshapes.cube import Cube


class PartialBlock(Cube):
    @property
    def blockshape(self) -> str:
        raise NotImplementedError

    def bounds(self, block: Block) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        return (0, 1), (0, 1), (0, 1)

    @property
    def do_not_cull(self) -> Tuple[bool, bool, bool, bool, bool, bool]:
        return False, False, False, False, False, False

    def get_block_model(self, block: Block, down: str, up: str, north: str, east: str, south: str, west: str, transparency: Tuple[bool, bool, bool, bool, bool, bool]) -> BlockMesh:
        bounds = self.bounds(block)
        return get_cube(
            down,
            up,
            north,
            east,
            south,
            west,
            2,
            bounds=bounds,
            texture_uv=(
                (bounds[0][0], bounds[2][0], bounds[0][1], bounds[2][1]),
                (bounds[0][0], bounds[2][0], bounds[0][1], bounds[2][1]),
                (bounds[0][0], 1-bounds[1][1], bounds[0][1], 1-bounds[1][0]),
                (bounds[2][0], 1-bounds[1][1], bounds[2][1], 1-bounds[1][0]),
                (bounds[0][0], 1-bounds[1][1], bounds[0][1], 1-bounds[1][0]),
                (bounds[2][0], 1-bounds[1][1], bounds[2][1], 1-bounds[1][0]),
            ),
            do_not_cull=self.do_not_cull
        )
