from typing import Tuple, Dict, Union, List
import itertools
import pyglet
import numpy
from pyglet.gl import *
from pyglet.image import TextureRegion

from amulet.api import paths
from amulet.api.block import Block

paths.FORMATS_DIR = r"./amulet/formats"
paths.DEFINITIONS_DIR = r"./amulet/version_definitions"
from amulet import world_loader

import minecraft_model_reader

cull_offset_dict = {'down': (0,-1,0), 'up': (0,1,0), 'north': (0,0,-1), 'east': (1,0,0), 'south': (0,0,1), 'west': (-1,0,0)}


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
		pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
		pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)


class RenderChunk:
	def __init__(self, batch, world, resource_pack, render_world, cx, cz):
		self.batch = batch
		self.cx = cx
		self.cz = cz
		try:
			blocks = world.get_chunk(cx, cz).blocks
		except:
			return

		vert_list = []
		# face_list = []
		tex_list = []
		texture_region: TextureRegion = None

		show_up = numpy.ones(blocks.shape, dtype=numpy.bool)
		show_down = numpy.ones(blocks.shape, dtype=numpy.bool)
		show_north = numpy.ones(blocks.shape, dtype=numpy.bool)
		show_south = numpy.ones(blocks.shape, dtype=numpy.bool)
		show_east = numpy.ones(blocks.shape, dtype=numpy.bool)
		show_west = numpy.ones(blocks.shape, dtype=numpy.bool)
		cull_x = blocks[1:, :, :] != blocks[:-1, :, :]
		cull_y = blocks[:, 1:, :] != blocks[:, :-1, :]
		cull_z = blocks[:, :, 1:] != blocks[:, :, :-1]
		show_up[:, :-1, :] = cull_y
		show_down[:, 1:, :] = cull_y
		show_north[:, :, 1:] = cull_z
		show_south[:, :, :-1] = cull_z
		show_east[:-1, :, :] = cull_x
		show_west[1:, :, :] = cull_x

		show_map = {'up': show_up, 'down': show_down, 'north': show_north, 'south': show_south, 'east': show_east, 'west': show_west}

		for block_temp_id in numpy.unique(blocks):
			block = world.block_manager[
				block_temp_id
			]
			model: minecraft_model_reader.MinecraftMesh = resource_pack.get_model(
				block,
				face_mode=4
			)
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
				vert_list.append(vert_list_)
				texture = model.texture_index[cull_dir]
				# TODO: not all faces in the same model have the same texture
				texture_region = render_world.get_texture(model.textures[texture[0]])
				texture_array = numpy.array(
					(
						((model.texture_coords[cull_dir][0::2] * texture_region.width) + texture_region.x) / render_world.texture_bin.texture_width,
						((model.texture_coords[cull_dir][1::2] * min(texture_region.height, texture_region.width)) + texture_region.y) / render_world.texture_bin.texture_height
					)
				)
				tex_list.append(numpy.tile(texture_array.T.ravel(), block_count))
		if len(vert_list) > 0:
			vert_list = numpy.concatenate(vert_list, axis=None)
			tex_list = numpy.concatenate(tex_list, axis=None)
		self.batch.add(
			int(len(vert_list)/3),
			pyglet.gl.GL_QUADS,
			TextureBindGroup(texture_region.owner),
			('v3f', vert_list),
			('t2f', tex_list)
		)


class RenderWorld:
	def __init__(self, batch, world_path: str, resource_packs: Union[str, List[str]]):
		self.batch = batch
		self.world = world_loader.load_world(world_path)
		self.chunks: Dict[Tuple[int, int], RenderChunk] = {}

		self.render_distance = 3
		self.busy = False

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

	def get_texture(self, namespace_and_path: Tuple[str, str]):
		if namespace_and_path not in self.textures:
			abs_texture_path = self.resource_pack.get_texture(namespace_and_path)
			image = pyglet.image.load(abs_texture_path)
			self.textures[namespace_and_path] = self.texture_bin.add(image)

		return self.textures[namespace_and_path]

	def draw(self):
		self.batch.draw()

	def update(self, x, z):
		if not self.busy:
			self.busy = True
			cx = int(x) >> 4
			cz = int(z) >> 4
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
				self.chunks[chunk] = RenderChunk(self.batch, self.world, self.resource_pack, self, cx, cz)

			self.busy = False

		# unload chunks outside the render distance
		# for cx, cz in self.chunks.keys():
		# 	if cx, cz
