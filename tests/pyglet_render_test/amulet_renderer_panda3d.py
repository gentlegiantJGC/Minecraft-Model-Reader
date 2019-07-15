import json
import os
import plistlib
import math
import itertools


import numpy
from PyTexturePacker import Packer
from direct.showbase.ShowBase import ShowBase, NodePath, GeomVertexArrayFormat, Geom, GeomVertexFormat, GeomVertexData, \
    GeomVertexWriter, GeomTriangles, Texture, SamplerState, GeomNode, Vec3, ModifierButtons, KeyboardButton, \
    MouseButton, Point3, TransparencyAttrib

from amulet.api import paths
from amulet.api.block import Block
from panda3d.bullet import BulletDebugNode, BulletWorld, BulletBoxShape, BulletRigidBodyNode

from java_block_model import MinecraftJavaModelHandler

paths.FORMATS_DIR = r"C:\Users\Ben\PycharmProjects\Unified-Minecraft-Editor\src\amulet\formats"
paths.DEFINITIONS_DIR = r"C:\Users\Ben\PycharmProjects\Unified-Minecraft-Editor\src\amulet\version_definitions"

from amulet import world_loader

NUM_BLOCKS = 25
MOUSE_SENSITIVITY = 150
SPEED = 0.35

#print(world_loader.load_world(r"C:\Users\Ben\PycharmProjects\Unified-Minecraft-Editor\tests\worlds\1.13 World"))

class App(ShowBase):

    def __init__(self, world_path):
        ShowBase.__init__(self)

        world = world_loader.load_world(world_path)

        self.disable_mouse()
        self.setFrameRateMeter(True)
        self.set_scene_graph_analyzer_meter(True)

        self.num = 0
        self.blocks = []

        self.mouse_held = False
        self.old_mouse_pos = [0, 0]

        self.scene = NodePath('world')
        self.scene.reparentTo(self.render)

        # Start raycast changes
        self.block_map = {}
        self.raycasting = False
        # End raycast changes

        array = GeomVertexArrayFormat()
        array.addColumn("vertex", 3, Geom.NTFloat64, Geom.CPoint)
        array.addColumn("texcoord", 2, Geom.NTFloat64, Geom.CTexcoord)

        vert_format = GeomVertexFormat()
        vert_format.addArray(array)
        registered_vert_format = GeomVertexFormat.registerFormat(vert_format)

        vdata = GeomVertexData('test', registered_vert_format, Geom.UHStatic)
        #vdata.setNumRows(8 * 16 ** 2)

        vertex = GeomVertexWriter(vdata, 'vertex')
        texcoord = GeomVertexWriter(vdata, 'texcoord')
        prim = GeomTriangles(Geom.UHStatic)

        packer = Packer.create(max_width=2 ** 15, max_height=2 ** 15, bg_color=0x000000ff, border_padding=0,
                               shape_padding=0, enable_rotated=False)
        # packer.pack([os.path.join(r"C:\Users\james_000\Documents\GitHub\Minecraft-Model-Reader", f'{tex}.png') for tex in model['texture_list']], 'texture_atlas')
        packer.pack(r"assets/minecraft/textures/block", 'texture_atlas')

        java_model_handler = MinecraftJavaModelHandler(
            [r"assets"])  # , r"C:\Users\james_000\Documents\GitHub\Minecraft-Model-Reader\3d_pack\assets"])
        # model = java_model_handler.get_model('minecraft:end_portal_frame[eye=true,facing=west]')
        # model = java_model_handler.get_model('minecraft:magenta_glazed_terracotta')
        # model = java_model_handler.get_model('minecraft:crafting_table')
        # model = java_model_handler.get_model('minecraft:damaged_anvil')
        # model = java_model_handler.get_model('minecraft:oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=true]')

        with open('texture_atlas.plist', 'rb') as f:
            texture_map = plistlib.load(f)
        texture_name_to_path = {os.path.splitext(texture_path)[0]: texture_path for texture_path in
                                texture_map['frames']}
        atlas_size = numpy.array(texture_map['metadata']['size'].replace('{', '').replace('}', '').split(','),
                                 numpy.float)
        self.tex: Texture = self.loader.loadTexture("texture_atlas.png")
        self.tex.setMagfilter(SamplerState.FT_nearest)

        x = z = 0
        with open(r"blocks.json") as f:
            blockstates = json.load(f)

        vert_count = 0

        for x, z in itertools.product(range(8), range(8)):
            for y in range(-255, 0):
                y = abs(y)

                if world.get_block(x,y,z).blockstate == "minecraft:air":
                    continue
                else:
                    block: Block = world.get_block(x,y,z)

                    block_string = block.base_name
                    if block.properties:
                        block_string += f'[{",".join([f"{prop}={val}" for prop, val in block.properties.items()])}]'

                    model = java_model_handler.get_model(block_string)

                    texture_scale = numpy.ones((len(model['texture_list']), 2), numpy.float)
                    texture_offset = numpy.zeros((len(model['texture_list']), 2), numpy.float)

                    for index, texture_path in enumerate(model['texture_list']):
                        texture_path2 = texture_name_to_path[os.path.basename(texture_path)]
                        img_frame = texture_map['frames'][texture_path2]['frame'].replace('{', '').replace('}',
                                                                                                           '').split(
                            ',')
                        texture_scale[index, :] = img_frame[2:]
                        texture_offset[index, :] = img_frame[:2]
                    texture_scale /= atlas_size
                    texture_offset /= atlas_size

                    for vert_group in model['verts'].values():
                        for vert in vert_group:
                            vertex.addData3f(vert[0] + z, -vert[2] + x, vert[1] + y)

                    for face_dir in model['texture_verts'].keys():
                        texture_slice = model['textures'][face_dir]
                        tvert_group = model['texture_verts'][face_dir] * texture_scale[texture_slice] + texture_offset[
                            texture_slice]
                        tvert_group[:, 1] *= -1
                        for tvert in tvert_group:
                            texcoord.addData2f(*tvert)

                    for face_group in model['faces'].values():
                        if len(face_group) > 0:
                            face_group += vert_count
                            for face in face_group:
                                try:
                                    prim.addVertices(*face)
                                except OverflowError as e:
                                    print(prim)
                                    print("++" * 16)
                                    print(face)
                                    print(x, y, z)
                                    print(block_string)
                                    raise e
                            vert_count = face_group.max() + 1

                    self.block_map[(z, x, y)] = block_string

                    break

        """
        for block_id in blockstates:
            for state in blockstates[block_id]['states']:
                block_string = block_id
                if 'properties' in state:
                    block_string += f'[{",".join([f"{prop}={val}" for prop, val in state["properties"].items()])}]'
                model = java_model_handler.get_model(block_string)

                texture_scale = numpy.ones((len(model['texture_list']), 2), numpy.float)
                texture_offset = numpy.zeros((len(model['texture_list']), 2), numpy.float)

                for index, texture_path in enumerate(model['texture_list']):
                    texture_path2 = texture_name_to_path[os.path.basename(texture_path)]
                    img_frame = texture_map['frames'][texture_path2]['frame'].replace('{', '').replace('}', '').split(
                        ',')
                    texture_scale[index, :] = img_frame[2:]
                    texture_offset[index, :] = img_frame[:2]
                texture_scale /= atlas_size
                texture_offset /= atlas_size

                for vert_group in model['verts'].values():
                    for vert in vert_group:
                        vertex.addData3f(vert[0] + x, -vert[2] + z, vert[1])

                for face_dir in model['texture_verts'].keys():
                    texture_slice = model['textures'][face_dir]
                    tvert_group = model['texture_verts'][face_dir] * texture_scale[texture_slice] + texture_offset[
                        texture_slice]
                    tvert_group[:, 1] *= -1
                    for tvert in tvert_group:
                        texcoord.addData2f(*tvert)

                for face_group in model['faces'].values():
                    if len(face_group) > 0:
                        face_group += vert_count
                        for face in face_group:
                            prim.addVertices(*face)
                        vert_count = face_group.max() + 1

                # Start raycast changes
                self.block_map[(x, z)] = block_string
                # End raycast changes

                x += 2
                if x > 64:
                    x = 0
                    z += 2
                    print(z)
        """

        geom = Geom(vdata)
        geom.addPrimitive(prim)

        node = GeomNode('gnode')
        node.addGeom(geom)

        nodePath = self.render.attachNewNode(node)
        nodePath.setTexture(self.tex, 1)
        nodePath.setTransparency(TransparencyAttrib.MAlpha)

        # Start raycast changes
        dbgNode = BulletDebugNode('Debug')
        dbgNode.showWireframe(True)
        dbgNode.showBoundingBoxes(True)

        self.dbg = dbgANode = self.render.attachNewNode(dbgNode)
        dbgANode.show()

        self.world = BulletWorld()
        self.world.setDebugNode(dbgANode.node())

        for c, block in self.block_map.items():
            shape = BulletBoxShape(Vec3(0.5, 0.5, 0.5))
            node = BulletRigidBodyNode(
                f'block|{c[0]}|{c[1]}')  # FIXME: Big hack since bullet rigidbodies don't know their position
            node.addShape(shape)

            nnode = self.render.attachNewNode(node)
            nnode.setPos(c[0] + 0.5, c[1] - 0.5, 0 + 0.5)

            self.world.attachRigidBody(node)
        # End raycast changes

        self.taskMgr.add(self.move_camera_task, "MoveCameraTask")
        # self.taskMgr.add(self.update, "updateTask")

        self.mouseWatcherNode.set_modifier_buttons(ModifierButtons())
        self.buttonThrowers[0].node().set_modifier_buttons(ModifierButtons())
        self._forward_button = KeyboardButton.ascii_key(b"w")
        self._backward_button = KeyboardButton.ascii_key(b"s")
        self._left_button = KeyboardButton.ascii_key(b"a")
        self._right_button = KeyboardButton.ascii_key(b"d")

        self._raycast_btn = KeyboardButton.ascii_key(b"r")
        self._up_button = KeyboardButton.space()
        self._down_button = KeyboardButton.shift()
        self._right_click = MouseButton.two()

        self.accept("mouse3", self.handle_mouse_pressed)
        self.accept("mouse3-up", self.handle_mouse_released)

    def move_camera_task(self, task):
        x, y, z = self.camera.getPos()
        yaw, pitch, roll = self.camera.getHpr()

        if self.mouse_held:
            mx, my = self.mouseWatcherNode.getMouseX(), self.mouseWatcherNode.getMouseY()

            dx, dy = mx - self.old_mouse_pos[0], my - self.old_mouse_pos[1]

            dx *= MOUSE_SENSITIVITY
            dy *= MOUSE_SENSITIVITY

            yaw -= dx
            pitch += dy

            if pitch > 90:
                pitch = 90
            elif pitch < -90:
                pitch = -90

            self.old_mouse_pos = mx, my

        elif self.mouseWatcherNode.hasMouse():
            self.old_mouse_pos = self.mouseWatcherNode.getMouseX(), self.mouseWatcherNode.getMouseY()

        if self.mouseWatcherNode.is_button_down(self._forward_button):
            x -= math.sin(math.radians(yaw)) * SPEED
            y += math.cos(math.radians(yaw)) * SPEED
        elif self.mouseWatcherNode.is_button_down(self._backward_button):
            x += math.sin(math.radians(yaw)) * SPEED
            y -= math.cos(math.radians(yaw)) * SPEED
        if self.mouseWatcherNode.is_button_down(self._left_button):
            x -= math.cos(math.radians(yaw)) * SPEED
            y -= math.sin(math.radians(yaw)) * SPEED
        elif self.mouseWatcherNode.is_button_down(self._right_button):
            x += math.cos(math.radians(yaw)) * SPEED
            y += math.sin(math.radians(yaw)) * SPEED

        if self.mouseWatcherNode.is_button_down(self._up_button):
            z += SPEED
        elif self.mouseWatcherNode.is_button_down(self._down_button):
            z -= SPEED

        self.camera.setPosHpr(x, y, z, yaw, pitch, 0)

        # Start raycast changes
        if self.mouseWatcherNode.is_button_down(self._raycast_btn) and not self.raycasting:
            self.raycasting = True
            # self.world.doPhysics(0.0) # Uncomment this to see collision boxes
            pMouse = self.mouseWatcherNode.getMouse()
            pFrom = Point3()
            pTo = Point3()
            self.camLens.extrude(pMouse, pFrom, pTo)

            pFrom = self.render.getRelativePoint(self.camera, pFrom)
            pTo = self.render.getRelativePoint(self.camera, pTo)

            result = self.world.rayTestClosest(pFrom, pTo)

            if result.hasHit():
                name = result.getNode().getName()
                identifier, x, z = name.split('|')
                x, z = int(x), int(z)

                print(f"Clicked on {self.block_map.get((x, z))}")
        elif not self.mouseWatcherNode.is_button_down(self._raycast_btn) and self.raycasting:
            self.raycasting = False
        # End raycast changes

        return task.cont

    def handle_mouse_pressed(self):
        self.mouse_held = True

    def handle_mouse_released(self):
        self.mouse_held = False


if __name__ == "__main__":
    #app = App(r"C:\Users\Ben\PycharmProjects\Unified-Minecraft-Editor\tests\worlds\1.13 World")
    app = App(r"C:\Users\Ben\Saved Games\Minecraft\1.13\saves\Amulet Rendering Test")
    app.run()