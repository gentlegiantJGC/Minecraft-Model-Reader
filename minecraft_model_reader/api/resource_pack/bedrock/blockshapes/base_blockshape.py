from typing import Tuple

from minecraft_model_reader.api.mesh.block import BlockMesh
from minecraft_model_reader.api import Block


class BaseBlockShape:
    @property
    def blockshape(self) -> str:
        raise NotImplementedError

    def is_valid(self, block: Block) -> bool:
        """Does the given block have the correct properties to use this blockshape"""
        raise NotImplementedError

    def texture_index(self, block: Block, aux_value: int) -> int:
        """The texture index to use within the list for the given Block"""
        raise NotImplementedError

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
        raise NotImplementedError
