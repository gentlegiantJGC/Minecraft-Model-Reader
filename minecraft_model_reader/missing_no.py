import itertools
import numpy
import minecraft_model_reader
from typing import Dict, Union


_box_coordinates = numpy.array(
	list(
		itertools.product(
			[0, 1],
			[0, 1],
			[0, 1]
		)
	)
)

_cube_face_lut = {  # This maps face direction to the verticies used (defined in cube_vert_lut)
	'down': numpy.array([0, 4, 5, 1]),
	'up': numpy.array([3, 7, 6, 2]),
	'north': numpy.array([4, 0, 2, 6]),
	'east': numpy.array([5, 4, 6, 7]),
	'south': numpy.array([1, 5, 7, 3]),
	'west': numpy.array([0, 1, 3, 2])
}

_texture_uv = numpy.array([0, 0, 1, 1], numpy.float)
_uv_slice = [0, 1, 2, 1, 2, 3, 0, 3]
_tri_face = numpy.array([0, 1, 2, 0, 2, 3], numpy.uint32)
_quad_face = numpy.array([0, 1, 2, 3], numpy.uint32)

_verts: Dict[Union[str, None], numpy.ndarray] = {}
_texture_coords = {}
_tint_verts = {}
_tri_faces = {}
_quad_faces = {}
_tri_texture_index: Dict[Union[str, None], numpy.ndarray] = {side: numpy.zeros(2, dtype=numpy.uint32) for side in ('down', 'up', 'north', 'east', 'south', 'west')}
_quad_texture_index: Dict[Union[str, None], numpy.ndarray] = {side: numpy.zeros(1, dtype=numpy.uint32) for side in ('down', 'up', 'north', 'east', 'south', 'west')}

for _face_dir in _cube_face_lut:
	_verts[_face_dir] = _box_coordinates[_cube_face_lut[_face_dir]].ravel(),  # vertex coordinates for this face
	_verts[_face_dir] = _verts[_face_dir][0]
	_texture_coords[_face_dir] = _texture_uv[_uv_slice]  # texture vertices
	_tint_verts[_face_dir] = numpy.zeros(4, dtype=numpy.bool)
	_tri_faces[_face_dir] = _tri_face
	_quad_faces[_face_dir] = _quad_face

missing_no_tris = minecraft_model_reader.MinecraftMesh(
	3,
	_verts,
	_texture_coords,
	_tint_verts,
	_tri_faces,
	_tri_texture_index,
	[('minecraft', 'missing_no')],
	0
)

missing_no_quads = minecraft_model_reader.MinecraftMesh(
	4,
	_verts,
	_texture_coords,
	_tint_verts,
	_quad_faces,
	_quad_texture_index,
	[('minecraft', 'missing_no')],
	0
)
