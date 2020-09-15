from typing import Tuple

from minecraft_model_reader.api.resource_pack.bedrock.blockshapes.partial_block import PartialBlock
from minecraft_model_reader.api import Block
import amulet_nbt


class Comparator(PartialBlock):
    @property
    def blockshape(self) -> str:
        return "comparator"

    def texture_index(self, aux_value: int) -> int:
        return (aux_value >> 3) & 1

    def bounds(self, block: Block) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        return (0, 1), (0, 2/16), (0, 1)

    @property
    def do_not_cull(self) -> Tuple[bool, bool, bool, bool, bool, bool]:
        return False, True, False, False, False, False

    # TODO: rotation support


BlockShape = Comparator()
