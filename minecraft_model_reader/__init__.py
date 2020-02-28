import os
from minecraft_model_reader.lib.log import log
from .api.minecraft_mesh import MinecraftMesh
from minecraft_model_reader.java.java_rp_handler import JavaRP, JavaRPHandler

path = os.path.dirname(__file__)
java_vanilla_fix = JavaRP(os.path.join(path, 'resource_packs', 'java_vanilla_fix'))
