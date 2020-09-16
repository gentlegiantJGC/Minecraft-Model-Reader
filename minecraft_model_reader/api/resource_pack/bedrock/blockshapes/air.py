from typing import Tuple

from minecraft_model_reader.api.mesh.block import BlockMesh
from minecraft_model_reader.api import Block
from minecraft_model_reader.api.resource_pack.bedrock.blockshapes.base_blockshape import (
    BaseBlockShape,
)


class Air(BaseBlockShape):
    @property
    def blockshape(self) -> str:
        return "air"

    def is_valid(self, block: Block) -> bool:
        """Does the given block have the correct properties to use this blockshape"""
        return True

    def texture_index(self, block: Block, aux_value: int) -> int:
        """The texture index to use within the list for the given Block"""
        return 0

    def get_block_model(
        self,
        block: Block,
        up: str,
        down: str,
        north: str,
        east: str,
        south: str,
        west: str,
        transparency: Tuple[bool, bool, bool, bool, bool, bool],
    ) -> BlockMesh:
        return BlockMesh(3, {}, {}, {}, {}, {}, (), 2)


BlockShape = Air()
