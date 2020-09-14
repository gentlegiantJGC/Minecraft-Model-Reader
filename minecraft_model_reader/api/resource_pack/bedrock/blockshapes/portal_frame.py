from typing import Tuple

from minecraft_model_reader.api.resource_pack.bedrock.blockshapes.partial_block import PartialBlock


class PortalFrame(PartialBlock):
    @property
    def blockshape(self) -> str:
        return "portal_frame"

    @property
    def bounds(self) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        return (0, 1), (0, 13/16), (0, 1)


BlockShape = PortalFrame()
