import os
import re
from typing import List, Dict, Union
from .api import comment_json
try:
	from amulet.api.block import Block
except:
	from .api.block import Block
import numpy
import copy
import math


def empty_model():
	return copy.deepcopy(
		{
			'verts': {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},
			'texture_verts': {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},
			'faces': {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},  # [[v1, v2, v3],]
			'textures': {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},  # [t,]
			'texture_list': []
		}
	)


def rotate_3d(verts, x, y, z, dx, dy, dz):
	sb, cb = math.sin(math.radians(x)), math.cos(math.radians(x))
	sh, ch = math.sin(math.radians(y)), math.cos(math.radians(y))
	sa, ca = math.sin(math.radians(z)), math.cos(math.radians(z))
	trmtx = numpy.array(
		[
			[ch * ca, -ch * sa * cb + sh * sb, ch * sa * sb + sh * cb],
			[sa, ca * cb, -ca * sb],
			[-sh * ca, sh * sa * cb + ch * sb, -sh * sa * sb + ch * cb]
		]
	)
	origin = numpy.array([dx, dy, dz])
	return numpy.matmul(verts - origin, trmtx) + origin


cube_face_lut = {  # This maps face direction to the verticies used (defined in cube_vert_lut)
	'down': [2, 6, 4, 0],
	'up': [1, 5, 7, 3],
	'north': [6, 2, 3, 7],  # TODO: work out the correct order of these last four
	'east': [4, 6, 7, 5],
	'south': [0, 4, 5, 1],
	'west': [2, 0, 1, 3]
}

cube_vert_lut = {  # This maps from vertex index to index in [minx, miny, minz, maxx, maxy, maxz]
	0: [0, 1, 5],
	1: [0, 4, 5],
	2: [0, 1, 2],
	3: [0, 4, 2],
	4: [3, 1, 5],
	5: [3, 4, 5],
	6: [3, 1, 2],
	7: [3, 4, 2],
}

# combines the above two to map from face to index in [minx, miny, minz, maxx, maxy, maxz]. Used to index a numpy array
# The above two have been kept separate because the merged result is unintuitive and difficult to edit.
cube_lut = {
	face_dir_: [
		vert_coord_ for vert_ in vert_index_ for vert_coord_ in cube_vert_lut[vert_]
	]
	for face_dir_, vert_index_ in cube_face_lut.items()
}

uv_lut = [0, 3, 2, 3, 2, 1, 0, 1]

# tvert_lut = {  # TODO: implement this for the cases where the UV is not defined
# 	'down': [],
# 	'up': [],
# 	'north': [],
# 	'east': [],
# 	'south': [],
# 	'west': []
# }

class MinecraftJavaModelHandler:
	properties_regex = re.compile(r"(?:,(?P<name>[a-z0-9_]+)=(?P<value>[a-z0-9_]+))")

	def __init__(self, asset_dirs: List[str]):
		self._models = {}
		self._asset_dirs = asset_dirs

	def reload_resources(self, asset_dirs: List[str]):
		self._models.clear()
		self._asset_dirs = asset_dirs

	def get_model(self, blockstate_str: str) -> dict:
		if blockstate_str not in self._models:
			self._models[blockstate_str] = self._parse_blockstate_link(*Block.parse_blockstate_string(blockstate_str))
		return copy.deepcopy(self._models[blockstate_str])

	@staticmethod
	def _missing_no():
		return {
			'verts': {side: numpy.zeros((0, 3), numpy.float) for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},
			'texture_verts': {side: numpy.zeros((0, 2), numpy.float) for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},
			'faces': {side: numpy.zeros((0, 3), numpy.uint32) for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},  # [[v1, v2, v3],]
			'textures': {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},  # [t,]
			'texture_list': []
		}

	def _parse_blockstate_link(self, namespace: str, base_name: str, properties: Dict[str, str]) -> dict:
		for asset_dir in reversed(self._asset_dirs):
			if namespace in os.listdir(asset_dir):
				if f'{base_name}.json' in os.listdir(os.path.join(asset_dir, namespace, 'blockstates')):
					try:
						blockstate = comment_json.from_file(os.path.join(asset_dir, namespace, 'blockstates', f'{base_name}.json'))
					except:
						continue

					if 'variants' in blockstate:
						for variant in blockstate['variants']:
							if variant == '':
								try:
									return self._load_block_model(namespace, blockstate['variants'][variant])
								except:
									pass
							else:
								properties_match = self.properties_regex.finditer(f',{variant}')
								if all(properties.get(match.group("name"), match.group("value")) == match.group("value") for match in properties_match):
									try:
										return self._load_block_model(namespace, blockstate['variants'][variant])
									except:
										pass

					elif 'multipart' in blockstate:
						multi_model = empty_model()
						vert_count = {side: 0 for side in ('down', 'up', 'north', 'east', 'south', 'west', None)}
						texture_count = 0
						for case in blockstate['multipart']:
							try:
								if 'when' in case:
									if 'OR' in case['when']:
										if not any(
											all(
												properties.get(prop, None) in val.split('|') for prop, val in prop_match.items()
											) for prop_match in case['when']['OR']
										):
											continue
									elif not all(
										properties.get(prop, None) in val.split('|') for prop, val in case['when'].items()
									):
										continue

								if 'apply' in case:
									try:
										temp_model = self._load_block_model(namespace, case['apply'])
										for face in ('down', 'up', 'north', 'east', 'south', 'west', None):
											multi_model['verts'][face].append(temp_model['verts'][face])
											multi_model['texture_verts'][face].append(temp_model['texture_verts'][face])
											multi_model['faces'][face].append(temp_model['faces'][face] + vert_count[face])
											vert_count[face] += len(temp_model['verts'][face])
											multi_model['textures'][face].append(temp_model['textures'][face] + texture_count)
										multi_model['texture_list'] += temp_model['texture_list']
										texture_count += len(temp_model['texture_list'])

									except:
										pass
							except:
								pass

						out_model = empty_model()
						for face in ('down', 'up', 'north', 'east', 'south', 'west', None):
							for attr, shape, dtype in (('verts', (0, 3), numpy.float), ('texture_verts', (0, 2), numpy.float), ('faces', (0, 3), numpy.uint32)):
								try:
									out_model[attr][face] = numpy.vstack(multi_model[attr][face])
								except:
									out_model[attr][face] = numpy.zeros(shape, dtype)

							texture_list, inverse = numpy.unique(multi_model['texture_list'], return_inverse=True)
							out_model['texture_list'] = list(texture_list)
							try:
								out_model['textures'][face] = inverse[numpy.hstack(multi_model['textures'][face])]
							except:
								out_model['textures'][face] = numpy.zeros((0,), numpy.uint32)
						return out_model

		return self._missing_no()

	def _load_block_model(self, namespace: str, blockstate: Union[dict, list]) -> dict:
		if isinstance(blockstate, list):
			blockstate = blockstate[0]
		if 'model' not in blockstate:
			raise Exception
		model_path = blockstate['model']
		rotx = blockstate.get('x', 0)
		roty = blockstate.get('y', 0)
		# uvlock = blockstate.get('uvlock', False)

		java_model = self._recursive_load_block_model(namespace, model_path)

		triangle_model = empty_model()
		texture_list = {}
		texture_count = 0

		vert_count = {side: 0 for side in ('down', 'up', 'north', 'east', 'south', 'west', None)}
		for element in java_model.get('elements', {}):
			element_faces = element.get('faces', {})

			corners = numpy.sort(numpy.array([element.get('to', [1, 0, 2]), element.get('from', [0, 1, 0])], numpy.float)/16, 0).ravel()

			for face_dir in element_faces:
				if face_dir in cube_lut:
					cull_dir = element_faces[face_dir].get('cullface', None)

					triangle_model['verts'][cull_dir].append(
						corners[cube_lut[face_dir]].reshape((-1, 3))
					)

					tex = element_faces[face_dir].get('texture', None)
					while isinstance(tex, str) and tex.startswith('#'):
						tex = java_model['textures'].get(tex[1:], None)
					tex = os.path.join('assets', namespace, 'textures', tex)
					if tex not in texture_list:
						texture_list[tex] = texture_count
						triangle_model['texture_list'].append(tex)
						texture_count += 1
					triangle_model['textures'][cull_dir] += [texture_list[tex]] * 4

					texture_uv = numpy.array(element_faces[face_dir].get('uv', [0, 0, 16, 16]), numpy.float)/16  # TODO: get the uv based on box location if not defined
					texture_rotation = element_faces[face_dir].get('rotation', 0)
					uv_slice = uv_lut[2 * int(texture_rotation/90):] + uv_lut[:2 * int(texture_rotation/90)]
					triangle_model['texture_verts'][cull_dir].append(texture_uv[uv_slice].reshape((-1, 2)))

					faces = numpy.array([[0, 1, 2], [0, 2, 3]], numpy.uint32)
					faces += vert_count[cull_dir]
					triangle_model['faces'][cull_dir].append(faces)

					vert_count[cull_dir] += 4

		for cull_dir in ('down', 'up', 'north', 'east', 'south', 'west', None):
			if len(triangle_model['verts'][cull_dir]) == 0:
				triangle_model['verts'][cull_dir] = numpy.zeros((0, 3), numpy.float)
				triangle_model['faces'][cull_dir] = numpy.zeros((0, 3), numpy.uint32)
				triangle_model['texture_verts'][cull_dir] = numpy.zeros((0, 2), numpy.float)
				triangle_model['textures'][cull_dir] = numpy.zeros((0,), numpy.uint32)
			else:
				triangle_model['verts'][cull_dir] = rotate_3d(numpy.vstack(triangle_model['verts'][cull_dir]), rotx, roty, 0, 0.5, 0.5, 0.5)  # TODO: rotate model based on uv_lock
				triangle_model['faces'][cull_dir] = numpy.vstack(triangle_model['faces'][cull_dir])
				triangle_model['texture_verts'][cull_dir] = numpy.vstack(triangle_model['texture_verts'][cull_dir])
				triangle_model['textures'][cull_dir] = numpy.array(triangle_model['textures'][cull_dir], numpy.uint32)

		return triangle_model

	def _recursive_load_block_model(self, namespace: str, model_path: str) -> dict:
		asset_dir = next(asset_dir_ for asset_dir_ in self._asset_dirs if os.path.isfile(os.path.join(asset_dir_, namespace, 'models', f'{model_path}.json')))
		model = comment_json.from_file(os.path.join(asset_dir, namespace, 'models', f'{model_path}.json'))
		if 'parent' in model:
			parent_model = self._recursive_load_block_model(namespace, model['parent'])
		else:
			parent_model = {}
		if 'textures' in model:
			if 'textures' not in parent_model:
				parent_model['textures'] = {}
			for key, val in model['textures'].items():
				parent_model['textures'][key] = val
		if 'elements' in model:
			parent_model['elements'] = model['elements']

		return parent_model


if __name__ == '__main__':
	java_model_handler = MinecraftJavaModelHandler(['assets', r"PureBDcraft 512x MC113\assets"])
	print(java_model_handler.get_model('minecraft:oak_stairs[facing=south,half=top,shape=straight,waterlogged=true]'))
