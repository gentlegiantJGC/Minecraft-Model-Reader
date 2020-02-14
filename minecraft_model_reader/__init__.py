import os
from .api.base_api import MinecraftMesh
from .java_rp_handler import JavaRP, JavaRPHandler

path = os.path.dirname(__file__)
java_vanilla_fix = JavaRP(os.path.join(path, 'resource_packs', 'java_vanilla_fix'))
