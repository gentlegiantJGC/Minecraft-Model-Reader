from typing import Tuple, Dict

from minecraft_model_reader.api.mesh.block import BlockMesh
from minecraft_model_reader.api import Block
from minecraft_model_reader.api.resource_pack.bedrock.blockshapes.cube import Cube
import amulet_nbt


class Piston(Cube):
    def is_valid(self, block: Block) -> bool:
        return isinstance(block.properties.get("facing_direction"), amulet_nbt.TAG_Int)

    @property
    def blockshape(self) -> str:
        return "piston"

    def texture_index(self, block: Block, aux_value: int) -> int:
        return 0

    @property
    def rotation_map(self) -> Dict[int, Tuple[int, int]]:
        return {0: (2, 0), 1: (0, 0), 2: (1, 2), 3: (1, 0), 4: (1, 1), 5: (1, 3)}

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
        rotation = self.rotation_map.get(
            block.properties["facing_direction"].py_data, (0, 0)
        )

        return (
            super()
            .get_block_model(block, down, up, north, east, south, west, transparency)
            .rotate(*rotation)
        )


BlockShape = Piston()
