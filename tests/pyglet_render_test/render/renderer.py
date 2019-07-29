from typing import List, Union
import pyglet
from pyglet.window import key


from render.keys import key_map
from render.world import RenderWorld

class Renderer(pyglet.window.Window):

	def __init__(self, world_path: str, resource_packs: Union[str, List[str]]):
		self.batch = pyglet.graphics.Batch()
		self.render_world = RenderWorld(self.batch, world_path, resource_packs)
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
		self.yaw, self.pitch = 0, 0
		self.mouse_speed = 0.05
		self.rotation_mode = False
		# self.fps_disp = pyglet.clock.ClockDisplay()  # this is undefined and throws an error

		pyglet.clock.schedule_interval(self.update, 1 / 60.0)

	def on_mouse_motion(self, x, y, dx, dy):
		if self.rotation_mode:
			self.pitch += self.mouse_speed * -dy
			self.pitch = min(max(-90, self.pitch), 90)
			self.yaw += self.mouse_speed * dx

	def on_mouse_press(self, x, y, button, modifiers):
		if button == pyglet.window.mouse.MIDDLE:
			self.rotation_mode = not self.rotation_mode
			self.set_exclusive_mouse(self.rotation_mode)

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
		self.render_world.update(self.x, -self.z)

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
		self.render_world.draw()
		# self.fps_disp.draw()

	def on_resize(self, width, height):
		pyglet.gl.glViewport(0, 0, width, height)
		pyglet.gl.glMatrixMode(pyglet.gl.GL_PROJECTION)
		pyglet.gl.glLoadIdentity()
		pyglet.gl.gluPerspective(90, width / float(height), .1, 1000)
		pyglet.gl.glMatrixMode(pyglet.gl.GL_MODELVIEW)
		return pyglet.event.EVENT_HANDLED
