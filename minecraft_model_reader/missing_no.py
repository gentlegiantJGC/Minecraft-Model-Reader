import itertools
import numpy
from .api.base_api import MinecraftMesh


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
	'up': numpy.array([2, 7, 6, 2]),
	'north': numpy.array([4, 0, 2, 6]),  # TODO: work out the correct order of these last four
	'east': numpy.array([5, 4, 6, 7]),
	'south': numpy.array([1, 5, 7, 3]),
	'west': numpy.array([0, 1, 3, 2])
}

_texture_uv = numpy.array([0, 0, 1, 1], numpy.float)
_uv_slice = [0, 3, 2, 3, 2, 1, 0, 1]
_tri_face = numpy.array([[0, 1, 2, 0], [0, 2, 3, 0]], numpy.uint32)
_quad_face = numpy.array([[0, 1, 2, 3, 0]], numpy.uint32)

_verts = {}
_tri_faces = {}
_quad_faces = {}

for _face_dir in _cube_face_lut:
	_verts[_face_dir] = (
		numpy.hstack(
			(
				_box_coordinates[_cube_face_lut[_face_dir]],  # vertex coordinates for this face
				_texture_uv[_uv_slice].reshape((-1, 2))  # texture vertices
			)
		)
	)
	_quad_face_table: numpy.ndarray = _quad_face
	_tri_face_table: numpy.ndarray = _tri_face
	_tri_face_table[:, -1] = 0
	_quad_face_table[:, -1] = 0
	_tri_faces[_face_dir] = _tri_face_table
	_quad_faces[_face_dir] = _quad_face_table

missing_no_tris = MinecraftMesh(
	_verts,
	_tri_faces,
	[('minecraft', 'missing_no')]
)

missing_no_quads = MinecraftMesh(
	_verts,
	_quad_faces,
	[('minecraft', 'missing_no')]
)
