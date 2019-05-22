import os
import re
from typing import List, Dict, Union
import comment_json
from api.block import Block
import numpy

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
			self._models[blockstate_str] = self._parse_model(*Block.parse_blockstate_string(blockstate_str))
		return self._models[blockstate_str]

	@staticmethod
	def _missing_no():
		return {
			'verts': {side: numpy.zeros((0, 3), numpy.float) for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},
			'texture_verts': {side: numpy.zeros((0, 2), numpy.float) for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},
			'faces': {side: numpy.zeros((0, 3), numpy.uint32) for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},  # [[v1, v2, v3],]
			'textures': {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},  # [t,]
			'texture_list': []
		}

	def _parse_model(self, namespace: str, base_name: str, properties: Dict[str, str]) -> dict:
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
						pass
						# TODO

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

		triangle_model = {
			'verts': {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},
			'texture_verts': {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},
			'faces': {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},  # [[v1, v2, v3],]
			'textures': {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},  # [t,]
			'texture_list': []
		}
		texture_list = {}
		texture_count = 0

		vert_count = {side: 0 for side in ('down', 'up', 'north', 'east', 'south', 'west', None)}
		for element in java_model.get('elements', {}):
			element_faces = element.get('faces', {})

			corners = numpy.sort(numpy.array([element.get('to', [1, 0, 2]), element.get('from', [0, 1, 0])], numpy.float)/16, 0).ravel()

			for face_dir in element_faces:
				if face_dir in cube_lut:
					cull_dir = element_faces[face_dir].get('cullface', None)

					triangle_model['verts'][cull_dir].append(corners[cube_lut[face_dir]].reshape((-1, 3)))

					tex = element_faces[face_dir].get('texture', None)
					while isinstance(tex, str) and tex.startswith('#'):
						tex = java_model['textures'].get(tex[1:], None)
					tex = os.path.join('assets', namespace, 'textures', tex)
					if tex not in texture_list:
						texture_list[tex] = texture_count
						triangle_model['texture_list'].append(tex)
						texture_count += 1
					triangle_model['textures'][cull_dir] += [texture_list[tex]] * 4

					texture_uv = numpy.array(element_faces[face_dir].get('uv', [0, 0, 16, 16]), numpy.float)/16
					texture_rotation = element_faces[face_dir].get('rotation', 0)
					uv_slice = uv_lut[int(texture_rotation/45):] + uv_lut[:int(texture_rotation/45)]
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
			else:
				triangle_model['verts'][cull_dir] = numpy.vstack(triangle_model['verts'][cull_dir])
				triangle_model['faces'][cull_dir] = numpy.vstack(triangle_model['faces'][cull_dir])
				triangle_model['texture_verts'][cull_dir] = numpy.vstack(triangle_model['texture_verts'][cull_dir])

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
	java_model_handler = MinecraftJavaModelHandler(['assets'])
	print(java_model_handler.get_model('minecraft:end_portal_frame[eye=true,facing=west]'))
