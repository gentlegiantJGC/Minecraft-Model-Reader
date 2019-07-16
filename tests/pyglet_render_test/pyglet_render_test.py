import pyglet
from render.renderer import Renderer

if __name__ == "__main__":
	app = Renderer('./test_world', './../../test_packs/Vanilla 1.13.2')
	pyglet.app.run()
