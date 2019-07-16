import pyglet

from pyglet.window import key

class Renderer(pyglet.window.Window):
    
    def __init__(self):
        super(Renderer, self).__init__()

        self.keys = key.KeyStateHandler()
        self.push_handlers(self.keys)

        self.proto_label = pyglet.text.Label("Pyglet Prototype Renderer", x=5, y=self.height - 15)
        self.position_label = pyglet.text.Label("", x=5, y=self.height - 30)

        self.block_batch = pyglet.graphics.Batch()

        self.x, self.y, self.z = 0, 0, 0
        self.fps_disp = pyglet.clock.ClockDisplay()

        pyglet.clock.schedule_interval(self.update, 1/60.0)

    def update(self, delta_time):

        if self.keys[key.D]:
            self.x += 1
        elif self.keys[key.A]:
            self.x -= 1

        if self.keys[key.SPACE]:
            self.y += 1
        elif self.keys[key.LSHIFT] or self.keys[key.RSHIFT]:
            self.y -= 1

        if self.keys[key.W]:
            self.z += 1
        elif self.keys[key.S]:
            self.z -= 1

        self.position_label.text = f"x = {self.x}, y = {self.y}, z = {self.z}"


    def on_draw(self):
        self.clear()
        self.proto_label.draw()
        self.position_label.draw()
        self.fps_disp.draw()




if __name__ == "__main__":
    app = Renderer()
    pyglet.app.run()