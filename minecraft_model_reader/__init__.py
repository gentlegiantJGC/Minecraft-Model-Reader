import os
from minecraft_model_reader.lib.log import log
from .api.minecraft_mesh import MinecraftMesh
from minecraft_model_reader.api.resource_pack import BaseRP, BaseRPHandler
from minecraft_model_reader.java.java_rp_handler import JavaRP, JavaRPHandler

path = os.path.dirname(__file__)
