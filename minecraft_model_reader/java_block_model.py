import os
from typing import List, Dict, Union
from .api.base_api import MinecraftMesh
try:
	from amulet.api.block import Block
except:
	from .api.block import Block
import numpy
import copy
import math


def empty_model():  # TODO: make this use MinecraftMesh
	return copy.deepcopy(
		{
			'verts': {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},
			'texture_verts': {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},
			'faces': {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},  # [[v1, v2, v3],]
			'textures': {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},  # [t,]
			'texture_list': []
		}
	)


def _missing_no():  # TODO: make this use MinecraftMesh
	return {
		'verts': {side: numpy.zeros((0, 3), numpy.float) for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},
		'texture_verts': {side: numpy.zeros((0, 2), numpy.float) for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},
		'faces': {side: numpy.zeros((0, 3), numpy.uint32) for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},  # [[v1, v2, v3],]
		'textures': {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)},  # [t,]
		'texture_list': []
	}


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


def _parse_blockstate_file(self, resource_pack, block: Block) -> dict:
	if (block.namespace, block.base_name) in resource_pack.blockstate_files:
		blockstate: dict = resource_pack.blockstate_files[(block.namespace, block.base_name)]
		if 'variants' in blockstate:
			for variant in blockstate['variants']:
				if variant == '':
					try:
						return _load_block_model(resource_pack, block, blockstate['variants'][variant])
					except:
						pass
				else:
					properties_match = Block.parameters_regex.finditer(f',{variant}')
					if all(block.properties.get(match.group("name"), match.group("value")) == match.group("value") for match in properties_match):
						try:
							return _load_block_model(resource_pack, block, blockstate['variants'][variant])
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
									block.properties.get(prop, None) in val.split('|') for prop, val in prop_match.items()
								) for prop_match in case['when']['OR']
							):
								continue
						elif not all(
							block.properties.get(prop, None) in val.split('|') for prop, val in case['when'].items()
						):
							continue

					if 'apply' in case:
						try:
							temp_model = _load_block_model(resource_pack, block, case['apply'])
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


def _load_block_model(resource_pack, block: Block, blockstate: Union[dict, list]) -> dict:
	if isinstance(blockstate, list):
		blockstate = blockstate[0]
	if 'model' not in blockstate:
		return _missing_no()
	model_path = blockstate['model']
	rotx = blockstate.get('x', 0)
	roty = blockstate.get('y', 0)
	# uvlock = blockstate.get('uvlock', False)

	java_model = _recursive_load_block_model(resource_pack, block, model_path)

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
				tex = os.path.join('assets', block.namespace, 'textures', tex)
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


def _recursive_load_block_model(resource_pack, block: Block, model_path: str) -> dict:
	if (block.namespace, model_path) in resource_pack.model_files:
		model = resource_pack.model_files[(block.namespace, model_path)]
		if isinstance(model_path, MinecraftMesh):
			return model

		if 'parent' in model:
			parent_model = _recursive_load_block_model(resource_pack, block, model['parent'])
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

	else:
		return _missing_no()


if __name__ == '__main__':
	java_model_handler = MinecraftJavaModelHandler(['assets', r"PureBDcraft 512x MC113\assets"])
	print(java_model_handler.get_model('minecraft:oak_stairs[facing=south,half=top,shape=straight,waterlogged=true]'))
