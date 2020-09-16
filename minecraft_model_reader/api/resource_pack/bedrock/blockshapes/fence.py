from typing import Tuple

from minecraft_model_reader.api.resource_pack.bedrock.blockshapes.partial_block import (
    PartialBlock,
)
from minecraft_model_reader.api import Block


class Fence(PartialBlock):
    @property
    def blockshape(self) -> str:
        return "fence"

    def bounds(
        self, block: Block
    ) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        return (6 / 16, 1 - 6 / 16), (0, 1), (6 / 16, 1 - 6 / 16)

    @property
    def do_not_cull(self) -> Tuple[bool, bool, bool, bool, bool, bool]:
        return False, False, True, True, True, True


BlockShape = Fence()
