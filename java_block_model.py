import os
import re
from typing import List, Dict, Union
import comment_json
from api.block import Block
import numpy


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
		return {'missing':'no'}

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
								properties_match = self.properties_regex.finditer(variant)
								if all(properties.get(match.group("name"), None) == match.group("value") for match in properties_match):
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
			'verts': [],
			'texture_verts': [],
			'faces': [],  # [[v1, v2, v3, t],]
			'textures': []
		}
		textures = {}
		texture_count = 1

		# cube_face_lookup = {
		# 	'down': (0, 2, 6, 4),
		# 	'up': (1, 5, 7, 3),
		# 	'north': (6, 2, 3, 7),  # TODO: work out the correct order of these last four
		# 	'east': (4, 6, 7, 5),
		# 	'south': (0, 4, 5, 1),
		# 	'west': (0, 1, 3, 2)
		# }
		#
		# cube_vert_lookup = {
		# 	0: (0, 1, 2),
		# 	1: (0, 4, 2),
		# 	2: (0, 1, 5),
		# 	3: (0, 4, 5),
		# 	4: (3, 1, 2),
		# 	5: (3, 4, 2),
		# 	6: (3, 1, 5),
		# 	7: (3, 4, 5),
		# }

		cube_lut = {
			'down': ((0, 1, 2), (0, 1, 5), (3, 1, 5), (3, 1, 2)),
			'up': ((0, 4, 2), (3, 4, 2), (3, 4, 5), (0, 4, 5)),
			'north': ((3, 1, 5), (0, 1, 5), (0, 4, 5), (3, 4, 5)),
			'east': ((3, 1, 2), (3, 1, 5), (3, 4, 5), (3, 4, 2)),
			'south': ((0, 1, 2), (3, 1, 2), (3, 4, 2), (0, 4, 2)),
			'west': ((0, 1, 2), (0, 4, 2), (0, 4, 5), (0, 1, 5))
		}

		vert_count = 0
		for element in java_model['elements']:
			element_vert_count = 0
			element_tri_count = 0
			element_faces = element.get('faces', {})
			quad_count = sum(face in element_faces for face in ('down', 'up', 'north', 'east', 'south', 'west'))
			verts = numpy.zeros((quad_count * 4, 3), numpy.float)
			faces = numpy.zeros((quad_count * 2, 4), numpy.uint32)

			corner1 = element.get('to', [0, 0, 0])
			corner2 = element.get('from', [0, 0, 0])
			corners = [
				min(corner1[0], corner2[0]),
				min(corner1[1], corner2[1]),
				min(corner1[2], corner2[2]),
				max(corner1[0], corner2[0]),
				max(corner1[1], corner2[1]),
				max(corner1[2], corner2[2]),
			]

			for face_dir, face_verts in cube_lut.items():
				if face_dir in element_faces:
					verts[element_vert_count:element_vert_count+4, :] = [[corners[ind] for ind in vert] for vert in face_verts]
					tex = element_faces[face_dir].get('texture', None)
					while isinstance(tex, str) and tex.startswith('#'):
						tex = java_model['textures'].get(tex[1:], None)
					if tex not in textures:
						textures[tex] = texture_count
						triangle_model['textures'].append(tex)
						texture_count += 1

					faces[element_tri_count:element_tri_count+2, :] = [[0, 1, 2, texture_count-1], [0, 2, 3, texture_count-1]]
					faces[element_tri_count:element_tri_count + 2, :-1] += element_vert_count + vert_count
					element_vert_count += 4
					element_tri_count += 2

			triangle_model['verts'].append(verts)
			triangle_model['faces'].append(faces)
			vert_count += element_vert_count

		if len(triangle_model['verts']) == 0:
			triangle_model['verts'] = numpy.zeros((0, 3), numpy.float)
			triangle_model['faces'] = numpy.zeros((0, 4), numpy.uint32)
		else:
			triangle_model['verts'] = numpy.concatenate(triangle_model['verts'])
			triangle_model['faces'] = numpy.concatenate(triangle_model['faces'])

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
	print(java_model_handler.get_model('minecraft:brown_carpet'))
