import os
import logging
from minecraft_model_reader.api.mesh.block.block_mesh import BlockMesh
from minecraft_model_reader.api.resource_pack import (
    BaseResourcePack,
    BaseResourcePackManager,
)

path = os.path.dirname(__file__)

from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions

# init a default logger
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
