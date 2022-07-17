from typing import Tuple

from minecraft_model_reader.api.resource_pack.bedrock.blockshapes.partial_block import (
    PartialBlock,
)
from minecraft_model_reader.api import Block
from minecraft_model_reader.api.mesh.block import BlockMesh


class Chest(PartialBlock):
    @property
    def blockshape(self) -> str:
        return "chest"

    def bounds(
        self, block: Block
    ) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        return (1 / 16, 15 / 16), (0, 14 / 16), (1 / 16, 15 / 16)

    def texture_index(self, block: Block, aux_value: int) -> int:
        return 0

    @property
    def do_not_cull(self) -> Tuple[bool, bool, bool, bool, bool, bool]:
        return False, True, True, True, True, True

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
    ) -> BlockMesh:
        rotation = {2: 2, 3: 0, 4: 1, 5: 3}.get(
            block.properties["facing_direction"].py_data, 0
        )

        return (
            super()
            .get_block_model(
                block, down, up, north, east, south, west, transparency, modify_uv=False
            )
            .rotate(0, rotation)
        )


BlockShape = Chest()
