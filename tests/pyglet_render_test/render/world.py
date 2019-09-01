import queue
import time
from typing import Tuple, Dict, Union, List
import itertools
import pyglet
import numpy
from pyglet.gl import *

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
		try:
			blocks: numpy.ndarray = world.get_chunk(cx, cz).blocks
		except:
			return

		blocks_ = numpy.zeros(blocks.shape + numpy.array((2, 0, 2)), blocks.dtype)
		blocks_[1:-1, :, 1:-1] = blocks

		for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
			try:
				blocks_temp: numpy.ndarray = world.get_chunk(cx+dx, cz+dz).blocks
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

		models: Dict[int, minecraft_model_reader.MinecraftMesh] = {block_temp_id: resource_pack.get_model(world.block_manager[block_temp_id], face_mode=4) for block_temp_id in numpy.unique(blocks_)}
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
				block_offsets = block_locations + (cx*16, 0, cz*16)

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
				if not render_world.texture_exists(cur_texture):
					queue_.put(("texture", cur_texture))
					render_world.queued_textures.append(cur_texture)
				queue_.put(("vertices", cur_texture, vert_list_, block_count, model.texture_coords[cull_dir][0::2], model.texture_coords[cull_dir][1::2]))


class RenderWorld:
	def __init__(self, world_path: str, resource_packs: Union[str, List[str]]):
		self.batch = pyglet.graphics.Batch()
		self.queue = queue.Queue()
		self.queued_textures = []
		self.queued_chunks = []
		self.busy = False
		self.world = world_loader.load_world(world_path)
		self.chunks: Dict[Tuple[int, int], RenderChunk] = {}
		self.group = None

		self.render_distance = 3

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
			if queue_item[0] == "texture":
				texture_to_add = queue_item[1]
				self.add_texture(texture_to_add)
				self.queued_textures.remove(texture_to_add)

			elif queue_item[0] == "vertices":
				cur_texture, vert_list_, block_count, width_coords, height_coords = queue_item[1:]
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
				self.batch.add(
					int(len(vert_list_)/3),
					pyglet.gl.GL_QUADS,
					self.group,
					('v3i/static', vert_list_),
					('t2f/static', tex_list_)
				)
		self.batch.draw()

	def get_chunk_in_range(self, x, z):
		cx = int(x) >> 4
		cz = int(z) >> 4

		sorted_chunks = sorted(
			itertools.product(
				range(cx-self.render_distance, cx+self.render_distance),
				range(cz - self.render_distance, cz + self.render_distance)
			),
			key=lambda chunk_coords: chunk_coords[0]**2 + chunk_coords[1] ** 2
		)

		for chunk in sorted_chunks:
			if chunk not in self.chunks and chunk not in self.queued_chunks:
				self.queued_chunks.append(chunk)
				return chunk
		return None

	def calculate_chunk(self, chunk):
		cx, cz = chunk
		self.chunks[chunk] = RenderChunk(self.queue, self.world, self.resource_pack, self, cx, cz)
		self.queued_chunks.remove(chunk)
		self.busy = False
