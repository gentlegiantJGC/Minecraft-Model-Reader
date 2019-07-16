from typing import Tuple, Dict, Union, List
import itertools

import minecraft_model_reader

from amulet.api import paths
from amulet.api.block import Block
paths.FORMATS_DIR = r"./amulet/formats"
paths.DEFINITIONS_DIR = r"./amulet/version_definitions"
from amulet import world_loader


class RenderWorld:
	def __init__(self, world_path: str, resource_packs: Union[str, List[str]]):
		self.world = world_loader.load_world(world_path)
		self.chunks: Dict[Tuple[int, int], RenderChunk] = {}

		self.render_distance = 2
		self.busy = False

		# Load the resource pack
		if isinstance(resource_packs, str):
			resource_packs = minecraft_model_reader.JavaRP(resource_packs)
		elif isinstance(resource_packs, list):
			resource_packs = [minecraft_model_reader.JavaRP(rp) for rp in resource_packs]
		else:
			raise Exception('resource_pack must be a string or list of strings')
		resource_pack = minecraft_model_reader.JavaRPHandler(resource_packs)

	def update(self, x, z):
		if not self.busy:
			self.busy = True
			cx = x >> 4
			cz = z >> 4
			chunk = next(
				(
					chunk for chunk in sorted(
						itertools.product(
							range(
								cx-self.render_distance,
								cx+self.render_distance
							),
							range(
								cz - self.render_distance,
								cz + self.render_distance
							)
						),
						key=lambda chunk_coords: chunk_coords[0]**2 + chunk_coords[1] ** 2
					) if chunk not in self.chunks
				),
				None
			)
			if chunk is None:  # All the chunks in the render distance have been loaded
				self.busy = False
			else:
				cx, cz = chunk
				blocks = self.world.get_chunk(cx, cz).blocks

			self.busy = False

		# unload chunks outside the render distance
		# for cx, cz in self.chunks.keys():
		# 	if cx, cz
