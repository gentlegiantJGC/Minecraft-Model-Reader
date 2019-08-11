from concurrent.futures.thread import ThreadPoolExecutor
from typing import List, Union
import pyglet
import math
from pyglet.window import key


from render.keys import key_map
from render.world import RenderWorld


class Renderer(pyglet.window.Window):
	def __init__(self, world_path: str, resource_packs: Union[str, List[str]]):
		self.render_world = RenderWorld(world_path, resource_packs)
		super(Renderer, self).__init__(480, 270, 'Amulet', resizable=True)
		self.set_minimum_size(240, 135)

		self.keys = key.KeyStateHandler()
		self.push_handlers(self.keys)

		self.proto_label = pyglet.text.Label("Pyglet Prototype Renderer", x=5, y=self.height - 15)
		self.position_label = pyglet.text.Label("", x=5, y=self.height - 30)

		pyglet.gl.glClearColor(0.2, 0.3, 0.2, 1.0)
		pyglet.gl.glEnable(pyglet.gl.GL_DEPTH_TEST)
		pyglet.gl.glDepthFunc(pyglet.gl.GL_LESS)

		self.x, self.y, self.z = 0, 0, 0
		self.move_speed = 1
		self.yaw, self.pitch = 0, 0
		self.mouse_speed = 0.05
		self.rotation_mode = False
		# self.fps_disp = pyglet.clock.ClockDisplay()  # this is undefined and throws an error

		pyglet.clock.schedule_interval(self.update, 1 / 60.0)

		self.thread_executor = ThreadPoolExecutor(max_workers=4)

	def on_mouse_motion(self, x, y, dx, dy):
		if self.rotation_mode:
			self.pitch += self.mouse_speed * -dy
			self.pitch = min(max(-90, self.pitch), 90)
			self.yaw += self.mouse_speed * dx

	def on_mouse_press(self, x, y, button, modifiers):
		if button == pyglet.window.mouse.MIDDLE:
			self.rotation_mode = not self.rotation_mode
			self.set_exclusive_mouse(self.rotation_mode)

	def on_close(self):
		super().on_close()
		self.thread_executor.shutdown()

	def update(self, delta_time):
		if self.keys[key_map['forwards']]:
			self.y -= self.move_speed * math.sin(math.radians(self.pitch))
			self.x += self.move_speed * math.cos(math.radians(self.pitch)) * math.sin(math.radians(self.yaw))
			self.z += self.move_speed * math.cos(math.radians(self.pitch)) * math.cos(math.radians(self.yaw))
		if self.keys[key_map['backwards']]:
			self.y += self.move_speed * math.sin(math.radians(self.pitch))
			self.x -= self.move_speed * math.cos(math.radians(self.pitch)) * math.sin(math.radians(self.yaw))
			self.z -= self.move_speed * math.cos(math.radians(self.pitch)) * math.cos(math.radians(self.yaw))

		if self.keys[key_map['left']]:
			self.z += self.move_speed * math.sin(math.radians(self.yaw))
			self.x -= self.move_speed * math.cos(math.radians(self.yaw))

		if self.keys[key_map['right']]:
			self.z -= self.move_speed * math.sin(math.radians(self.yaw))
			self.x += self.move_speed * math.cos(math.radians(self.yaw))

		if self.keys[key_map['up']]:
			self.y += self.move_speed
		if self.keys[key_map['down']]:
			self.y -= self.move_speed

		# self.proto_label.y = self.height - 15
		# self.position_label.y = self.height - 30
		# self.position_label.text = f"x = {self.x}, y = {self.y}, z = {self.z}"

		chunk_to_calculate = self.render_world.get_chunk_in_range(self.x, -self.z)
		if chunk_to_calculate is not None:
			self.thread_executor.submit(self.render_world.calculate_chunk, chunk_to_calculate)

	# def on_resize(self, width, height):
	# 	print('hi')
	# 	self.proto_label.y = self.height - 15
	# 	self.position_label.y = height - 30
	# 	self.on_draw()

	def on_draw(self):
		# self.clear()
		pyglet.gl.glClear(pyglet.gl.GL_COLOR_BUFFER_BIT | pyglet.gl.GL_DEPTH_BUFFER_BIT)
		pyglet.gl.glLoadIdentity()
		pyglet.gl.glRotatef(self.pitch, 1, 0, 0)
		pyglet.gl.glRotatef(self.yaw, 0, 1, 0)
		pyglet.gl.glTranslatef(-self.x, -self.y, self.z)
		# self.proto_label.draw()
		# self.position_label.draw()
		self.render_world.draw(1 / 60.0)
		# self.fps_disp.draw()

	def on_resize(self, width, height):
		pyglet.gl.glViewport(0, 0, width, height)
		pyglet.gl.glMatrixMode(pyglet.gl.GL_PROJECTION)
		pyglet.gl.glLoadIdentity()
		pyglet.gl.gluPerspective(90, width / float(height), .1, 1000)
		pyglet.gl.glMatrixMode(pyglet.gl.GL_MODELVIEW)
		return pyglet.event.EVENT_HANDLED
