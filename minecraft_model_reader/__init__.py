import os
from .java_rp_handler import JavaRP, JavaRPHandler
from .api.minecraft_mesh import MinecraftMesh

path = os.path.dirname(__file__)
java_vanilla_fix = JavaRP(os.path.join(path, 'resource_packs', 'java_vanilla_fix'))
