from typing import Tuple

from minecraft_model_reader.api.mesh.block import BlockMesh
from minecraft_model_reader.api import Block
from minecraft_model_reader.api.mesh.block.cube import get_cube
from minecraft_model_reader.api.resource_pack.bedrock.blockshapes.cube import Cube


class PartialBlock(Cube):
    @property
    def blockshape(self) -> str:
        raise NotImplementedError

    @property
    def bounds(self) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        return (0, 1), (0, 1), (0, 1)

    def get_block_model(self, block: Block, down: str, up: str, north: str, east: str, south: str, west: str, transparency: Tuple[bool, bool, bool, bool, bool, bool]) -> BlockMesh:
        return get_cube(
            down,
            up,
            north,
            east,
            south,
            west,
            2,
            bounds=self.bounds,
            texture_uv=(
                (self.bounds[0][0], self.bounds[2][0], self.bounds[0][1], self.bounds[2][1]),
                (self.bounds[0][0], self.bounds[2][0], self.bounds[0][1], self.bounds[2][1]),
                (self.bounds[0][0], 1-self.bounds[1][1], self.bounds[0][1], 1-self.bounds[1][0]),
                (self.bounds[2][0], 1-self.bounds[1][1], self.bounds[2][1], 1-self.bounds[1][0]),
                (self.bounds[0][0], 1-self.bounds[1][1], self.bounds[0][1], 1-self.bounds[1][0]),
                (self.bounds[2][0], 1-self.bounds[1][1], self.bounds[2][1], 1-self.bounds[1][0]),
            )
        )
