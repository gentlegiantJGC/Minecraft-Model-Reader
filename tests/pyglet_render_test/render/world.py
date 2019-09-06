import queue
import time
from typing import Tuple, Dict, Union, List
import itertools
import pyglet
import numpy
from pyglet.gl import *
import random
import uuid

from amulet.api import paths

paths.FORMATS_DIR = r"./amulet/formats"
paths.DEFINITIONS_DIR = r"./amulet/version_definitions"
from amulet import world_loader

import minecraft_model_reader

cull_offset_dict = {'down': (0, -1, 0), 'up': (0, 1, 0), 'north': (0, 0, -1), 'east': (1, 0, 0), 'south': (0, 0, 1), 'west': (-1, 0, 0)}


# The following two classes are from the docs and might already exist in pyglet
class TextureEnableGroup(pyglet.graphics.Group):
	def set_state(self):
		glEnable(GL_TEXTURE_2D)
		glEnable(GL_CULL_FACE)

	def unset_state(self):
		glDisable(GL_TEXTURE_2D)
		glDisable(GL_CULL_FACE)


texture_enable_group = TextureEnableGroup()


class TextureBindGroup(pyglet.graphics.Group):
	def __init__(self, texture):
		super(TextureBindGroup, self).__init__(parent=texture_enable_group)
		self.texture = texture

	def set_state(self):
		glBindTexture(GL_TEXTURE_2D, self.texture.id)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


class RenderChunk:
	def __init__(self, queue_: queue.Queue, world, resource_pack, render_world, cx, cz):
		self.cx = cx
		self.cz = cz
		self.queue = queue_
		self.world = world
		self.resource_pack = resource_pack
		self.render_world = render_world
		self.render_data = []
		self.render_lod = None
		self.render_id = None  # used so that if the queue still contains data from the previous geometry it knows to discard that data

	def unload(self):
		self.render_id = uuid.uuid4()
		for data in self.render_data:
			data.delete()
		self.render_data = []

	def needs_rebuild(self, px, pz, render_distance) -> bool:
		return self.get_lod(px, pz, render_distance) != self.render_lod

	def get_lod(self, px, pz, render_distance) -> int:
		distance = max(abs(self.cx - px / 16), abs(self.cz - pz / 16))
		for lod in range(3):
			if distance <= render_distance[lod]:
				return lod

	def tessellate(self, px, pz, render_distance):
		lod = self.get_lod(px, pz, render_distance)
		if self.render_lod == 0:
			if lod == 2:
				self.render_lod = 2
				self._create_lod2()
		elif self.render_lod in [1, 2]:
			if lod == 0:
				self.render_lod = 0
				self._create_lod0()
		elif self.render_lod is None:
			if lod == 0:
				self.render_lod = 0
				self._create_lod0()
			elif lod == 1:
				self.render_lod = 1
				self._create_lod2()
			elif lod == 2:
				self.render_lod = 2
				self._create_lod2()
		else:
			self.unload()
			del self

	def _create_lod0(self):
		self.unload()
		try:
			blocks: numpy.ndarray = self.world.get_chunk(self.cx, self.cz).blocks
		except:
			return
		blocks_ = numpy.zeros(blocks.shape + numpy.array((2, 0, 2)), blocks.dtype)
		blocks_[1:-1, :, 1:-1] = blocks

		for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
			try:
				blocks_temp: numpy.ndarray = self.world.get_chunk(self.cx+dx, self.cz+dz).blocks
				if (dx, dz) == (-1, 0):
					blocks_[0, :, 1:-1] = blocks_temp[-1, :, :]
				elif (dx, dz) == (1, 0):
					blocks_[-1, :, 1:-1] = blocks_temp[0, :, :]
				elif (dx, dz) == (0, -1):
					blocks_[1:-1, :, 0] = blocks_temp[:, :, -1]
				elif (dx, dz) == (0, 1):
					blocks_[1:-1, :, -1] = blocks_temp[:, :, 0]

			except:
				continue

		models: Dict[int, minecraft_model_reader.MinecraftMesh] = {block_temp_id: self.resource_pack.get_model(self.world.block_manager[block_temp_id], face_mode=4) for block_temp_id in numpy.unique(blocks_)}
		is_transparrent = [block_temp_id for block_temp_id, model in models.items() if not model.is_opaque]
		is_transparrent_array = numpy.isin(blocks_, is_transparrent)

		show_up = numpy.ones(blocks.shape, dtype=numpy.bool)
		show_down = numpy.ones(blocks.shape, dtype=numpy.bool)
		show_up[:, :-1, :] = is_transparrent_array[1:-1, 1:, 1:-1]
		show_down[:, 1:, :] = is_transparrent_array[1:-1, :-1, 1:-1]
		show_north = is_transparrent_array[1:-1, :, :-2]
		show_south = is_transparrent_array[1:-1, :-1, 2:]
		show_east = is_transparrent_array[2:, :-1, 1:-1]
		show_west = is_transparrent_array[:-2, :-1, 1:-1]

		show_map = {'up': show_up, 'down': show_down, 'north': show_north, 'south': show_south, 'east': show_east, 'west': show_west}

		for block_temp_id in numpy.unique(blocks):
			model: minecraft_model_reader.MinecraftMesh = models[block_temp_id]
			all_block_locations = numpy.argwhere(blocks == block_temp_id)
			where = None
			for cull_dir in model.faces.keys():
				if cull_dir is None:
					block_locations = all_block_locations
				elif cull_dir in show_map:
					if where is None:
						where = tuple(all_block_locations.T)
					block_locations = all_block_locations[show_map[cull_dir][where]]
					if len(block_locations) == 0:
						continue
				else:
					continue

				block_count = len(block_locations)
				block_offsets = block_locations + (self.cx*16, 0, self.cz*16)

				# the vertices in model space
				verts = model.verts[cull_dir]
				# translate the vertices to world space
				vert_list_ = numpy.tile(verts, (block_count, 1))
				for axis in range(3):
					vert_list_[:, axis::3] += block_offsets[:, axis].reshape((-1, 1))
				vert_list_ = vert_list_.flatten().astype(int)
				texture = model.texture_index[cull_dir]
				# TODO: not all faces in the same model have the same texture
				cur_texture = model.textures[texture[0]]
				if not self.render_world.texture_exists(cur_texture):
					self.queue.put(("texture", (self.cx, self.cz), self.render_id, cur_texture))
					self.render_world.queued_textures.append(cur_texture)
				self.queue.put(("vertices", (self.cx, self.cz), self.render_id, cur_texture, vert_list_, block_count, model.texture_coords[cull_dir][0::2], model.texture_coords[cull_dir][1::2]))

	def _create_lod2(self):
		self.unload()
		try:
			blocks: numpy.ndarray = self.world.get_chunk(self.cx, self.cz).blocks
		except:
			return

		models: Dict[int, minecraft_model_reader.MinecraftMesh] = {block_temp_id: self.resource_pack.get_model(self.world.block_manager[block_temp_id], face_mode=4) for block_temp_id in numpy.unique(blocks)}

		is_transparrent = [block_temp_id for block_temp_id, model in models.items() if not model.is_opaque]
		is_transparrent_array = numpy.isin(blocks, is_transparrent)
		is_visible_array = numpy.zeros(blocks.shape, numpy.int8)
		is_visible_array[:] = -2
		is_visible_array[1:-1, :, 1:-1] = 0
		is_visible_array[:, :-1, :] += is_transparrent_array[:, 1:, :]
		is_visible_array[:, 1:, :] += is_transparrent_array[:, :-1, :]
		is_visible_array[:, :, 1:] += is_transparrent_array[:, :, :-1]
		is_visible_array[:, :, :-1] += is_transparrent_array[:, :, 1:]
		is_visible_array[:-1, :, :] += is_transparrent_array[1:, :, :]
		is_visible_array[1:, :, :] += is_transparrent_array[:-1, :, :]
		is_visible_array = is_visible_array > 0

		for block_temp_id in numpy.unique(blocks):
			model: minecraft_model_reader.MinecraftMesh = models[block_temp_id]
			if model.is_opaque:
				all_block_locations = numpy.argwhere(numpy.all([blocks == block_temp_id, is_visible_array], axis=0)) + (self.cx * 16, 0, self.cz * 16)
				self.queue.put(("points", (self.cx, self.cz), self.render_id, all_block_locations.ravel().astype(int), tuple(random.randrange(0, 256) for _ in range(3))))


class RenderWorld:
	def __init__(self, world_path: str, resource_packs: Union[str, List[str]]):
		self.batch = pyglet.graphics.Batch()
		self.queue = queue.Queue()
		self.queued_textures = []
		self.queued_chunks = []
		self.world = world_loader.load_world(world_path)
		self.chunks: Dict[Tuple[int, int], RenderChunk] = {}
		self.group = None

		self.render_distance = [5, 10, 15]
		self.render_distance[1] = max(self.render_distance[0], self.render_distance[1])
		self.render_distance[2] = max(self.render_distance[1], self.render_distance[2])

		# Load the resource pack
		if isinstance(resource_packs, str):
			resource_packs = minecraft_model_reader.JavaRP(resource_packs)
		elif isinstance(resource_packs, list):
			resource_packs = [minecraft_model_reader.JavaRP(rp) for rp in resource_packs]
		else:
			raise Exception('resource_pack must be a string or list of strings')
		self.resource_pack = minecraft_model_reader.JavaRPHandler(resource_packs)
		self.textures = {}
		self.texture_bin = pyglet.image.atlas.TextureBin()

	def texture_exists(self, namespace_and_path: Tuple[str, str]):
		return namespace_and_path in self.textures or namespace_and_path in self.queued_textures

	def add_texture(self, namespace_and_path: Tuple[str, str]):
		abs_texture_path = self.resource_pack.get_texture(namespace_and_path)
		image = pyglet.image.load(abs_texture_path)
		self.textures[namespace_and_path] = self.texture_bin.add(image)

	def draw(self, start_time, dt):
		while not self.queue.empty() and time.clock() - start_time < dt:
			queue_item = self.queue.get()
			if queue_item[1] in self.chunks:
				chunk = self.chunks[queue_item[1]]
				if chunk.render_id != queue_item[2]:
					continue
			else:
				continue

			if queue_item[0] == "texture":
				texture_to_add = queue_item[3]
				self.add_texture(texture_to_add)
				self.queued_textures.remove(texture_to_add)

			elif queue_item[0] == "vertices":
				cur_texture, vert_list_, block_count, width_coords, height_coords = queue_item[3:]
				texture_region = self.textures[cur_texture]
				if self.group is None:
					self.group = TextureBindGroup(texture_region.owner)
				texture_array = numpy.array(
					(
						((width_coords * texture_region.width) + texture_region.x) / self.texture_bin.texture_width,
						((height_coords * min(texture_region.height, texture_region.width)) + texture_region.y) / self.texture_bin.texture_height
					)
				)
				tex_list_ = numpy.tile(texture_array.T.ravel(), block_count)
				chunk.render_data.append(
					self.batch.add(
						int(len(vert_list_)/3),
						pyglet.gl.GL_QUADS,
						self.group,
						('v3i/static', vert_list_),
						('t2f/static', tex_list_)
					)
				)
			elif queue_item[0] == "points":
				vert_list_, colour = queue_item[3:]
				pyglet.gl.glPointSize(5)
				chunk.render_data.append(
					self.batch.add(
						len(vert_list_) // 3,
						pyglet.gl.GL_POINTS,
						None,
						('v3i/static', vert_list_),
						('c3B/static', colour * (len(vert_list_) // 3)),
					)
				)
		self.batch.draw()

	def get_chunk_in_range(self, x, z):
		cx = int(x) >> 4
		cz = int(z) >> 4

		sorted_chunks = sorted(
			itertools.product(
				range(cx-self.render_distance[-1], cx+self.render_distance[-1]),
				range(cz - self.render_distance[-1], cz + self.render_distance[-1])
			),
			key=lambda chunk_coords: (chunk_coords[0]-cx)**2 + (chunk_coords[1]-cz) ** 2
		)

		for chunk in sorted_chunks:
			if (chunk not in self.chunks or self.chunks[chunk].needs_rebuild(x, z, self.render_distance)) and chunk not in self.queued_chunks:
				self.queued_chunks.append(chunk)
				return chunk
		return None

	def calculate_chunk(self, chunk, px, pz):
		cx, cz = chunk
		if chunk not in self.chunks:
			self.chunks[chunk] = RenderChunk(self.queue, self.world, self.resource_pack, self, cx, cz)
		self.chunks[chunk].tessellate(px, -pz, self.render_distance)
		self.queued_chunks.remove(chunk)
