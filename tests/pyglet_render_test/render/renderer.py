from typing import List, Union
import pyglet
from pyglet.window import key
import itertools


from render.keys import key_map
from render.world import RenderWorld

import minecraft_model_reader




class Renderer(pyglet.window.Window):

	def __init__(self, world_path: str, resource_packs: Union[str, List[str]]):
		self.render_world = RenderWorld(world_path, resource_packs)
		super(Renderer, self).__init__(480, 270, 'Amulet', resizable=True)
		self.set_minimum_size(240, 135)

		self.keys = key.KeyStateHandler()
		self.push_handlers(self.keys)

		self.proto_label = pyglet.text.Label("Pyglet Prototype Renderer", x=5, y=self.height - 15)
		self.position_label = pyglet.text.Label("", x=5, y=self.height - 30)

		self.block_batch = pyglet.graphics.Batch()

		self.x, self.y, self.z = 0, 0, 0
		# self.fps_disp = pyglet.clock.ClockDisplay()  # this is undefined and throws an error

		pyglet.clock.schedule_interval(self.update, 1 / 60.0)


	def update(self, delta_time):

		if self.keys[key_map['right']]:
			self.x += 1
		elif self.keys[key_map['left']]:
			self.x -= 1

		if self.keys[key_map['up']]:
			self.y += 1
		elif self.keys[key_map['down']]:
			self.y -= 1

		if self.keys[key_map['forwards']]:
			self.z += 1
		elif self.keys[key_map['backwards']]:
			self.z -= 1

		self.proto_label.y = self.height - 15
		self.position_label.y = self.height - 30
		self.position_label.text = f"x = {self.x}, y = {self.y}, z = {self.z}"
		self.render_world.update(self.x, self.z)

	# def on_resize(self, width, height):
	# 	print('hi')
	# 	self.proto_label.y = self.height - 15
	# 	self.position_label.y = height - 30
	# 	self.on_draw()

	def on_draw(self):
		self.clear()
		# self.triangle.verts.draw(pyglet.gl.GL_TRIANGLES)
		self.proto_label.draw()
		self.position_label.draw()
		# self.fps_disp.draw()
