from typing import Union, Iterable, Dict, Tuple, Optional
import itertools
from minecraft_model_reader import MinecraftMesh
from minecraft_model_reader.lib.missing_no import missing_no_tris, missing_no_quads
try:
	from amulet.api.block import Block
except:
	from minecraft_model_reader.api.block import Block
import numpy
import math
import copy
import amulet_nbt

FACE_KEYS = ('down', 'up', 'north', 'east', 'south', 'west', None)


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


def merge_models(models: Iterable[MinecraftMesh], face_mode: int = 3) -> MinecraftMesh:
	textures = []
	texture_count = 0
	vert_count = {side: 0 for side in FACE_KEYS}
	verts = {side: [] for side in FACE_KEYS}
	tverts = {side: [] for side in FACE_KEYS}
	tint_verts = {side: [] for side in FACE_KEYS}
	faces = {side: [] for side in FACE_KEYS}
	texture_indexes = {side: [] for side in FACE_KEYS}
	transparent = 2

	for temp_model in models:
		for cull_dir in temp_model.faces.keys():
			verts[cull_dir].append(temp_model.verts[cull_dir])
			tverts[cull_dir].append(temp_model.texture_coords[cull_dir])
			tint_verts[cull_dir].append(temp_model.tint_verts[cull_dir])
			face_table = temp_model.faces[cull_dir].copy()
			texture_index = temp_model.texture_index[cull_dir].copy()
			face_table += vert_count[cull_dir]
			texture_index += texture_count
			faces[cull_dir].append(face_table)
			texture_indexes[cull_dir].append(texture_index)

			vert_count[cull_dir] += int(temp_model.verts[cull_dir].shape[0] / temp_model.face_mode)

		textures += temp_model.textures
		texture_count += len(temp_model.textures)
		transparent = min(transparent, temp_model.is_transparent)

	if textures:
		textures, texture_index_map = numpy.unique(textures, return_inverse=True, axis=0)
		texture_index_map = texture_index_map.astype(numpy.uint32)
		textures = list(zip(textures.T[0], textures.T[1]))
	else:
		texture_index_map = numpy.array([], dtype=numpy.uint8)

	remove_faces = []
	for cull_dir, face_table in faces.items():
		if verts[cull_dir]:
			verts[cull_dir] = numpy.concatenate(verts[cull_dir], axis=None)
			tverts[cull_dir] = numpy.concatenate(tverts[cull_dir], axis=None)
			tint_verts[cull_dir] = numpy.concatenate(tint_verts[cull_dir], axis=None)
		else:
			verts[cull_dir] = numpy.zeros((0, 3), numpy.float)
			tverts[cull_dir] = numpy.zeros((0, 2), numpy.float)
			tint_verts[cull_dir] = numpy.zeros(0, numpy.float)

		if face_table:
			faces[cull_dir] = numpy.concatenate(face_table, axis=None)
			texture_indexes[cull_dir] = texture_index_map[numpy.concatenate(texture_indexes[cull_dir], axis=None)]
		else:
			remove_faces.append(cull_dir)

	for cull_dir in remove_faces:
		del faces[cull_dir]
		del verts[cull_dir]
		del tverts[cull_dir]
		del texture_indexes[cull_dir]

	return MinecraftMesh(face_mode, verts, tverts, tint_verts, faces, texture_indexes, textures, transparent)


def get_model(resource_pack, block: Block, face_mode: int = 3) -> MinecraftMesh:
	"""A function to load the model for a block from a resource pack.
	Needs a JavaRPHandler and Block.
	See get_model in JavaRPHandler if you are trying to use from an external application."""
	if block.extra_blocks:
		return merge_models(
			(_get_model(resource_pack, block.base_block, face_mode), ) +
			tuple(_get_model(resource_pack, block_, face_mode) for block_ in block.extra_blocks)
		)
	else:
		return _get_model(resource_pack, block, face_mode)


def _get_model(resource_pack, block: Block, face_mode: int = 3) -> MinecraftMesh:
	"""Get a model for a Block object with no extra blocks"""
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
					if all(block.properties.get(match.group("name"), amulet_nbt.TAG_String(match.group("value"))).value == match.group("value") for match in properties_match):
						try:
							return _load_blockstate_model(resource_pack, block, blockstate['variants'][variant], face_mode)
						except:
							pass

		elif 'multipart' in blockstate:
			models = []

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
								[amulet_nbt.TAG_String(s) for s in val.split('|')] if isinstance(val, str)
								else ([amulet_nbt.TAG_String('true')] if val else [amulet_nbt.TAG_String('false')]) if isinstance(val, bool)
								else Exception
							) for prop, val in case['when'].items()
						):
							continue

					if 'apply' in case:
						try:
							models.append(_load_blockstate_model(resource_pack, block, case['apply'], face_mode))

						except:
							pass
				except:
					pass

			return merge_models(models)

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

uv_lut = [0, 3, 2, 3, 2, 1, 0, 1]

# tvert_lut = {  # TODO: implement this for the cases where the UV is not defined
# 	'down': [],
# 	'up': [],
# 	'north': [],
# 	'east': [],
# 	'south': [],
# 	'west': []
# }


def create_cull_map() -> Dict[Tuple[int, int], Dict[Optional[str], Optional[str]]]:
	cull_remap_ = {}
	roty_map = ["north", "east", "south", "west"]
	for roty in range(-3, 4):
		for rotx in range(-3, 4):
			roty_map_rotated = roty_map[roty:] + roty_map[:roty]
			rotx_map = [roty_map_rotated[0], "down", roty_map_rotated[2], "up"]
			rotx_map_rotated = rotx_map[rotx:] + rotx_map[:rotx]
			roty_remap = dict(zip(roty_map, roty_map_rotated))
			rotx_remap = dict(zip(rotx_map, rotx_map_rotated))
			cull_remap_[(roty, rotx)] = {
				key: rotx_remap.get(roty_remap.get(key, key), roty_remap.get(key, key)) for key in FACE_KEYS
			}
	return cull_remap_


cull_remap_all = create_cull_map()


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
	rotx = int(blockstate_value.get('x', 0)//90)
	roty = int(blockstate_value.get('y', 0)//90)
	uvlock = blockstate_value.get('uvlock', False)

	model = copy.deepcopy(_load_block_model(resource_pack, block, model_path, face_mode))

	# TODO: rotate model based on uv_lock
	if rotx or roty and (roty, rotx) in cull_remap_all:
		cull_remap = cull_remap_all[(roty, rotx)]
		return MinecraftMesh(
			model.face_mode,
			{
				cull_remap[cull_dir]: rotate_3d(
					rotate_3d(
						model.verts[cull_dir].reshape((-1, model.face_mode)),
						rotx*90, 0, 0, 0.5, 0.5, 0.5),
					0, roty*90, 0, 0.5, 0.5, 0.5).ravel()
				for cull_dir in model.verts
			},
			{cull_remap[cull_dir]: model.texture_coords[cull_dir] for cull_dir in model.texture_coords},
			{cull_remap[cull_dir]: model.tint_verts[cull_dir] for cull_dir in model.tint_verts},
			{cull_remap[cull_dir]: model.faces[cull_dir] for cull_dir in model.faces},
			{cull_remap[cull_dir]: model.texture_index[cull_dir] for cull_dir in model.texture_index},
			model.textures,
			model.is_transparent
		)
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
	vert_count = {side: 0 for side in FACE_KEYS}
	verts = {side: [] for side in FACE_KEYS}
	tverts = {side: [] for side in FACE_KEYS}
	tint_verts = {side: [] for side in FACE_KEYS}
	faces = {side: [] for side in FACE_KEYS}
	
	texture_indexes = {side: [] for side in FACE_KEYS}
	transparent = 2

	for element in java_model.get('elements', {}):
		# iterate through elements (one cube per element)
		element_faces = element.get('faces', {})

		opaque_face_count = 0
		if transparent and 'rotation' not in element and element.get('to', [16, 16, 16]) == [16, 16, 16] and element.get('from', [0, 0, 0]) == [0, 0, 0] and len(element_faces) >= 6:
			# if the block is not yet defined as a solid block
			# and this element is a full size element
			# check if the texture is opaque
			transparent = 1
			check_faces = True
		else:
			check_faces = False

		# lower and upper box coordinates
		corners = numpy.sort(
			numpy.array(
				[
					element.get('to', [16, 16, 16]),
					element.get('from', [0, 0, 0])
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

		for face_dir in element_faces:
			if face_dir in cube_face_lut:
				# get the cull direction. If there is an opaque block in this direction then cull this face
				cull_dir = element_faces[face_dir].get('cullface', None)

				# get the relative texture path for the texture used
				texture_path = element_faces[face_dir].get('texture', None)
				while isinstance(texture_path, str) and texture_path.startswith('#'):
					texture_path = java_model['textures'].get(texture_path[1:], None)

				if check_faces:
					if resource_pack.texture_is_transparent(block.namespace, texture_path):
						check_faces = False
					else:
						opaque_face_count += 1

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
				face_verts = box_coordinates[cube_face_lut[face_dir]]
				if 'rotation' in element:
					rotation = element['rotation']
					origin = [r/16 for r in rotation.get('origin', [8, 8, 8])]
					angle = rotation.get('angle', 0)
					axis = rotation.get('axis', 'x')
					angles = [0, 0, 0]
					if axis == 'x':
						angles[0] = -angle
					elif axis == 'y':
						angles[1] = -angle
					elif axis == 'z':
						angles[2] = -angle
					face_verts = rotate_3d(face_verts, *angles, *origin)

				verts[cull_dir].append(
					face_verts  # vertex coordinates for this face
				)

				tverts[cull_dir].append(
					texture_uv[uv_slice].reshape((-1, 2))  # texture vertices
				)
				if 'tintindex' in element_faces[face_dir]:
					tint_verts[cull_dir] += [0, 1, 0] * 4  # TODO: set this up for each supported block
				else:
					tint_verts[cull_dir] += [1, 1, 1] * 4

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

		if opaque_face_count == 6:
			transparent = 0

	remove_faces = []
	for cull_dir, face_array in faces.items():
		if len(face_array) > 0:
			faces[cull_dir] = numpy.concatenate(face_array, axis=None)
			tint_verts[cull_dir] = numpy.concatenate(tint_verts[cull_dir], axis=None)
			verts[cull_dir] = numpy.concatenate(verts[cull_dir], axis=None)
			tverts[cull_dir] = numpy.concatenate(tverts[cull_dir], axis=None)
			texture_indexes[cull_dir] = numpy.array(texture_indexes[cull_dir], dtype=numpy.uint32)
		else:
			remove_faces.append(cull_dir)

	for cull_dir in remove_faces:
		del faces[cull_dir]
		del tint_verts[cull_dir]
		del verts[cull_dir]
		del tverts[cull_dir]
		del texture_indexes[cull_dir]

	model = resource_pack.model_files[(block.namespace, model_path)] = MinecraftMesh(face_mode, verts, tverts, tint_verts, faces, texture_indexes, textures, transparent)

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
