import numpy

from minecraft_model_reader.api.mesh.block import BlockMesh
from minecraft_model_reader.api import Block
from minecraft_model_reader.api.resource_pack.bedrock.blockshapes.default import Default


class Flat(Default):
    @property
    def tint(self) -> tuple[float, float, float]:
        return 1, 1, 1

    def get_block_model(
        self,
        block: Block,
        down: str,
        up: str,
        north: str,
        east: str,
        south: str,
        west: str,
        transparency: tuple[bool, bool, bool, bool, bool, bool],
    ) -> BlockMesh:
        return BlockMesh(
            3,
            {
                None: numpy.array(
                    [
                        0.0,
                        0.0625,
                        1.0,
                        1.0,
                        0.0625,
                        1.0,
                        1.0,
                        0.0625,
                        0.0,
                        0.0,
                        0.0625,
                        0.0,
                    ],
                    dtype=numpy.float32,
                )
            },
            {
                None: numpy.array(
                    [0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0], numpy.float32
                )
            },
            {None: numpy.array(self.tint * 4, numpy.float32)},
            {None: numpy.array([0, 1, 2, 0, 2, 3], numpy.uint32)},
            {None: numpy.array([0, 0], numpy.uint32)},
            (up,),
            2,
        )
