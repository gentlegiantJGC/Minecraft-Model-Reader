from minecraft_model_reader.api import Block
from minecraft_model_reader.api.resource_pack.bedrock.blockshapes.door import Door


class Door6(Door):
    @property
    def blockshape(self) -> str:
        return "door6"

    def texture_index(self, block: Block, aux_value: int) -> int:
        return 6


BlockShape = Door6()
