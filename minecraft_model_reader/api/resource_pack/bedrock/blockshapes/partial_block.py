from typing import Tuple

from minecraft_model_reader.api.mesh.block import BlockMesh
from minecraft_model_reader.api import Block
from minecraft_model_reader.api.mesh.block.cube import get_cube
from minecraft_model_reader.api.resource_pack.bedrock.blockshapes.default import Default

BoundsType = Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]
DoNotCullType = Tuple[bool, bool, bool, bool, bool, bool]


class PartialBlock(Default):
    def bounds(self, block: Block) -> BoundsType:
        return (0, 1), (0, 1), (0, 1)

    @property
    def do_not_cull(self) -> DoNotCullType:
        return False, False, False, False, False, False

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
        modify_uv=True,
        bounds: BoundsType = None,
        do_not_cull: DoNotCullType = None,
    ) -> BlockMesh:
        bounds = bounds or self.bounds(block)
        if modify_uv:
            uv = (
                (bounds[0][0], bounds[2][0], bounds[0][1], bounds[2][1]),
                (bounds[0][0], bounds[2][0], bounds[0][1], bounds[2][1]),
                (bounds[0][0], 1 - bounds[1][1], bounds[0][1], 1 - bounds[1][0]),
                (bounds[2][0], 1 - bounds[1][1], bounds[2][1], 1 - bounds[1][0]),
                (bounds[0][0], 1 - bounds[1][1], bounds[0][1], 1 - bounds[1][0]),
                (bounds[2][0], 1 - bounds[1][1], bounds[2][1], 1 - bounds[1][0]),
            )
        else:
            uv = ((0, 0, 1, 1),) * 6
        return get_cube(
            down,
            up,
            north,
            east,
            south,
            west,
            2,
            bounds=bounds,
            texture_uv=uv,
            do_not_cull=do_not_cull or self.do_not_cull,
        )
