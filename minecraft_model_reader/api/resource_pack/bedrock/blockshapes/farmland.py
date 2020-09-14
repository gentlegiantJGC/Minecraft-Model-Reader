from typing import Tuple

from minecraft_model_reader.api.resource_pack.bedrock.blockshapes.partial_block import PartialBlock


class FarmLand(PartialBlock):
    @property
    def blockshape(self) -> str:
        return "farmland"

    @property
    def bounds(self) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        return (0, 1), (0, 15/16), (0, 1)


BlockShape = FarmLand()
