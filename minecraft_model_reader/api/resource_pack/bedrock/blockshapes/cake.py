from typing import Tuple

from minecraft_model_reader.api.resource_pack.bedrock.blockshapes.partial_block import (
    PartialBlock,
)
from minecraft_model_reader.api import Block
from minecraft_model_reader.api.mesh.block import BlockMesh
import amulet_nbt


class Cake(PartialBlock):
    def is_valid(self, block: Block) -> bool:
        return isinstance(block.properties.get("bite_counter"), amulet_nbt.TAG_Int)

    @property
    def blockshape(self) -> str:
        return "cake"

    def bounds(
        self, block: Block
    ) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        return (
            (1 / 16 + block.properties["bite_counter"].value * 2 / 16, 15 / 16),
            (0, 0.5),
            (1 / 16, 15 / 16),
        )

    def texture_index(self, block: Block, aux_value: int) -> int:
        return min(block.properties["bite_counter"].value, 1)

    @property
    def do_not_cull(self) -> Tuple[bool, bool, bool, bool, bool, bool]:
        return False, True, True, True, True, True


BlockShape = Cake()
