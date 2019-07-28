from typing import Union
import itertools
from minecraft_model_reader import MinecraftMesh
from .missing_no import missing_no_tris, missing_no_quads
try:
	from amulet.api.block import Block
except:
	from .api.block import Block
import numpy
import math
import copy


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


def get_model(resource_pack, block: Block, face_mode: int = 3) -> MinecraftMesh:
	"""A function to load the model for a block from a resource pack.
	Needs a JavaRPHandler and Block.
	See get_model in JavaRPHandler if you are trying to use from an external application."""
	assert face_mode in [3, 4], 'face_mode is the number of verts per face. It must be 3 or 4'
	if (block.namespace, block.base_name) in resource_pack.blockstate_files:
		blockstate: dict = resource_pack.blockstate_files[(block.namespace, block.base_name)]
		if 'variants' in blockstate:
			for variant in blockstate['variants']:
				if variant == '':
					try:
						return _load_blockstate_model(resource_pack, block, blockstate['variants'][variant], face_mode)
					except:
						pass
				else:
					properties_match = Block.parameters_regex.finditer(f',{variant}')
					if all(block.properties.get(match.group("name"), match.group("value")) == match.group("value") for match in properties_match):
						try:
							return _load_blockstate_model(resource_pack, block, blockstate['variants'][variant], face_mode)
						except:
							pass

		elif 'multipart' in blockstate:
			textures = []
			texture_count = 0
			vert_count = {side: 0 for side in ('down', 'up', 'north', 'east', 'south', 'west', None)}
			verts = {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)}
			tverts = {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)}
			faces = {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)}
			texture_indexes = {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)}

			for case in blockstate['multipart']:
				try:
					if 'when' in case:
						if 'OR' in case['when']:
							if not any(
								all(
									block.properties.get(prop, None) in (
											val.split('|') if isinstance(val, str)
											else (['true'] if val else ['false']) if isinstance(val, bool)
											else Exception
									) for prop, val in prop_match.items()
								) for prop_match in case['when']['OR']
							):
								continue
						elif not all(
							block.properties.get(prop, None) in (
								val.split('|') if isinstance(val, str)
								else (['true'] if val else ['false']) if isinstance(val, bool)
								else Exception
							) for prop, val in case['when'].items()
						):
							continue

					if 'apply' in case:
						try:
							temp_model = _load_blockstate_model(resource_pack, block, case['apply'], face_mode)

							for cull_dir in temp_model.faces.keys():
								verts[cull_dir].append(temp_model.verts[cull_dir])
								tverts[cull_dir].append(temp_model.texture_coords[cull_dir])
								face_table = temp_model.faces[cull_dir].copy()
								texture_index = temp_model.texture_index[cull_dir].copy()
								face_table += vert_count[cull_dir]
								texture_index += texture_count
								faces[cull_dir].append(face_table)
								texture_indexes[cull_dir].append(texture_index)

								vert_count[cull_dir] += int(temp_model.verts[cull_dir].shape[0]/temp_model.face_mode)

							textures += temp_model.textures
							texture_count += len(temp_model.textures)

						except:
							pass
				except:
					pass

			if len(textures) > 0:
				textures, texture_index_map = numpy.unique(textures, return_inverse=True, axis=0)
				texture_index_map = texture_index_map.astype(numpy.uint32)
				textures = list(zip(textures.T[0], textures.T[1]))
			else:
				texture_index_map = numpy.array([], dtype=numpy.uint8)

			remove_faces = []
			for cull_dir, face_table in faces.items():
				if len(verts[cull_dir]) > 0:
					verts[cull_dir] = numpy.concatenate(verts[cull_dir], axis=None)
					tverts[cull_dir] = numpy.concatenate(tverts[cull_dir], axis=None)
				else:
					verts[cull_dir] = numpy.zeros((0, 3), numpy.float)
					tverts[cull_dir] = numpy.zeros((0, 2), numpy.float)

				if len(face_table) > 0:
					faces[cull_dir] = numpy.concatenate(face_table, axis=None)
					texture_indexes[cull_dir] = texture_index_map[numpy.concatenate(texture_indexes[cull_dir], axis=None)]
				else:
					remove_faces.append(cull_dir)

			for cull_dir in remove_faces:
				del faces[cull_dir]
				del verts[cull_dir]
				del tverts[cull_dir]
				del texture_indexes[cull_dir]

			return MinecraftMesh(face_mode, verts, tverts, faces, texture_indexes, textures)

	if face_mode == 4:
		return missing_no_quads
	else:
		return missing_no_tris


cube_face_lut = {  # This maps face direction to the verticies used (defined in cube_vert_lut)
	'down': numpy.array([0, 4, 5, 1]),
	'up': numpy.array([3, 7, 6, 2]),
	'north': numpy.array([4, 0, 2, 6]),
	'east': numpy.array([5, 4, 6, 7]),
	'south': numpy.array([1, 5, 7, 3]),
	'west': numpy.array([0, 1, 3, 2])
}
tri_face = numpy.array([0, 1, 2, 0, 2, 3], numpy.uint32)
quad_face = numpy.array([0, 1, 2, 3], numpy.uint32)

# cube_vert_lut = {  # This maps from vertex index to index in [minx, miny, minz, maxx, maxy, maxz]
# 	1: [0, 1, 5],
# 	3: [0, 4, 5],
# 	0: [0, 1, 2],
# 	2: [0, 4, 2],
# 	5: [3, 1, 5],
# 	7: [3, 4, 5],
# 	4: [3, 1, 2],
# 	6: [3, 4, 2],
# }
#
# # combines the above two to map from face to index in [minx, miny, minz, maxx, maxy, maxz]. Used to index a numpy array
# # The above two have been kept separate because the merged result is unintuitive and difficult to edit.
# cube_lut = {
# 	face_dir_: [
# 		vert_coord_ for vert_ in vert_index_ for vert_coord_ in cube_vert_lut[vert_]
# 	]
# 	for face_dir_, vert_index_ in cube_face_lut.items()
# }

uv_lut = [0, 1, 2, 1, 2, 3, 0, 3]

# tvert_lut = {  # TODO: implement this for the cases where the UV is not defined
# 	'down': [],
# 	'up': [],
# 	'north': [],
# 	'east': [],
# 	'south': [],
# 	'west': []
# }


def _load_blockstate_model(resource_pack, block: Block, blockstate_value: Union[dict, list], face_mode: int = 3) -> MinecraftMesh:
	assert face_mode in [3, 4], 'face_mode is the number of verts per face. It must be 3 or 4'
	if isinstance(blockstate_value, list):
		blockstate_value = blockstate_value[0]
	if 'model' not in blockstate_value:
		if face_mode == 4:
			return missing_no_quads
		else:
			return missing_no_tris
	model_path = blockstate_value['model']
	rotx = blockstate_value.get('x', 0)
	roty = blockstate_value.get('y', 0)
	uvlock = blockstate_value.get('uvlock', False)

	model = copy.deepcopy(_load_block_model(resource_pack, block, model_path, face_mode))

	# TODO: rotate model based on uv_lock
	if rotx != 0 or roty != 0:
		for cull_dir in model.verts:
			model.verts[cull_dir].setflags(write=True)
			model.verts[cull_dir] = rotate_3d(model.verts[cull_dir].reshape((-1, model.face_mode)), rotx, roty, 0, 0.5, 0.5, 0.5).ravel()
			model.verts[cull_dir].setflags(write=False)
	return model


def _load_block_model(resource_pack, block: Block, model_path: str, face_mode: int = 3) -> MinecraftMesh:

	# recursively load model files into one dictionary
	java_model = _recursive_load_block_model(resource_pack, block, model_path, face_mode)

	# return immediately if it is already a MinecraftMesh class. This could be because it is missing_no or a forge model if implemented
	if isinstance(java_model, MinecraftMesh):
		return copy.deepcopy(java_model)

	# set up some variables
	texture_dict = {}
	textures = []
	texture_count = 0
	vert_count = {side: 0 for side in ('down', 'up', 'north', 'east', 'south', 'west', None)}
	verts = {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)}
	tverts = {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)}
	faces = {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)}
	texture_indexes = {side: [] for side in ('down', 'up', 'north', 'east', 'south', 'west', None)}

	for element in java_model.get('elements', {}):
		# iterate through elements (one cube per element)
		element_faces = element.get('faces', {})

		# lower and upper box coordinates
		corners = numpy.sort(
			numpy.array(
				[
					element.get('to', [1, 0, 2]),
					element.get('from', [0, 1, 0])
				],
				numpy.float
			)/16,
			0
		)

		# vertex coordinates of the box
		box_coordinates = numpy.array(
			list(
				itertools.product(
					corners[:, 0],
					corners[:, 1],
					corners[:, 2]
				)
			)
		)
		# TODO: box rotation

		for face_dir in element_faces:
			if face_dir in cube_face_lut:
				# get the cull direction. If there is an opaque block in this direction then cull this face
				cull_dir = element_faces[face_dir].get('cullface', None)

				# get the relative texture path for the texture used
				texture_path = element_faces[face_dir].get('texture', None)
				while isinstance(texture_path, str) and texture_path.startswith('#'):
					texture_path = java_model['textures'].get(texture_path[1:], None)

				# get the texture
				if texture_path not in texture_dict:
					texture_dict[texture_path] = texture_count
					textures.append((block.namespace, texture_path))
					texture_count += 1

				# texture index for the face
				texture_index = texture_dict[texture_path]

				# get the uv values for each vertex
				# TODO: get the uv based on box location if not defined
				texture_uv = numpy.array(element_faces[face_dir].get('uv', [0, 0, 16, 16]), numpy.float)/16
				texture_rotation = element_faces[face_dir].get('rotation', 0)
				uv_slice = uv_lut[2 * int(texture_rotation / 90):] + uv_lut[:2 * int(texture_rotation / 90)]

				# merge the vertex coordinates and texture coordinates
				verts[cull_dir].append(
					box_coordinates[cube_face_lut[face_dir]]  # vertex coordinates for this face
				)

				tverts[cull_dir].append(
					texture_uv[uv_slice].reshape((-1, 2))  # texture vertices
				)

				# merge the face indexes and texture index
				if face_mode == 4:
					face_table = quad_face + vert_count[cull_dir]
					texture_indexes[cull_dir] += [texture_index]
				else:
					face_table = tri_face + vert_count[cull_dir]
					texture_indexes[cull_dir] += [texture_index, texture_index]

				# faces stored under cull direction because this is the criteria to render them or not
				faces[cull_dir].append(face_table)

				vert_count[cull_dir] += 4

	remove_faces = []
	for cull_dir, face_array in faces.items():
		if len(face_array) > 0:
			faces[cull_dir] = numpy.concatenate(face_array, axis=None)
			verts[cull_dir] = numpy.concatenate(verts[cull_dir], axis=None)
			tverts[cull_dir] = numpy.concatenate(tverts[cull_dir], axis=None)
			texture_indexes[cull_dir] = numpy.array(texture_indexes[cull_dir], dtype=numpy.uint32)
		else:
			remove_faces.append(cull_dir)

	for cull_dir in remove_faces:
		del faces[cull_dir]
		del verts[cull_dir]
		del tverts[cull_dir]
		del texture_indexes[cull_dir]

	model = resource_pack.model_files[(block.namespace, model_path)] = MinecraftMesh(face_mode, verts, tverts, faces, texture_indexes, textures)

	return model


def _recursive_load_block_model(resource_pack, block: Block, model_path: str, face_mode: int = 3) -> Union[dict, MinecraftMesh]:
	if (block.namespace, model_path) in resource_pack.model_files:
		model = resource_pack.model_files[(block.namespace, model_path)]
		if isinstance(model, MinecraftMesh):
			return model

		if 'parent' in model:
			parent_model = _recursive_load_block_model(resource_pack, block, model['parent'], face_mode)
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
		if face_mode == 4:
			return missing_no_quads
		else:
			return missing_no_tris
