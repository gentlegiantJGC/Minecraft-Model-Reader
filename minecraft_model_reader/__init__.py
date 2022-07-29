import os
import minecraft_model_reader.api._log
from minecraft_model_reader.api.mesh.block.block_mesh import BlockMesh
from minecraft_model_reader.api.resource_pack import (
    BaseResourcePack,
    BaseResourcePackManager,
)

path = os.path.dirname(__file__)

from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions
