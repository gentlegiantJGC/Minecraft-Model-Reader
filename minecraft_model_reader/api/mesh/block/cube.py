from typing import Dict, Tuple, Optional
import numpy
import itertools

from minecraft_model_reader.api.mesh.block.block_mesh import FACE_KEYS, BlockMesh


unit_box_coordinates = numpy.array(list(itertools.product([0, 1], [0, 1], [0, 1])))  # X, Y, Z
cube_face_lut = {  # This maps face direction to the vertices used (defined in unit_box_coordinates)
    "down": numpy.array([0, 4, 5, 1]),
    "up": numpy.array([3, 7, 6, 2]),
    "north": numpy.array([4, 0, 2, 6]),
    "east": numpy.array([5, 4, 6, 7]),
    "south": numpy.array([1, 5, 7, 3]),
    "west": numpy.array([0, 1, 3, 2]),
}
tri_face = numpy.array([0, 1, 2, 0, 2, 3], numpy.uint32)

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

uv_rotation_lut = [0, 3, 2, 3, 2, 1, 0, 1]  # remap


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
                key: rotx_remap.get(roty_remap.get(key, key), roty_remap.get(key, key))
                for key in FACE_KEYS
            }
    return cull_remap_


cull_remap_all = create_cull_map()


def _create_unit_cube_attrs():
    _texture_uv = numpy.array([0, 0, 1, 1], numpy.float)
    _verts: Dict[str, numpy.ndarray] = {}
    _texture_coords = {}
    _tint_verts = {}
    _tri_faces = {}
    for _face_dir in cube_face_lut:
        _verts[_face_dir] = unit_box_coordinates[
            cube_face_lut[_face_dir]
        ].ravel()  # vertex coordinates for this face
        _texture_coords[_face_dir] = _texture_uv[uv_rotation_lut]  # texture vertices
        _tint_verts[_face_dir] = numpy.ones(12, dtype=numpy.float)
        _tri_faces[_face_dir] = tri_face
    return _verts, _texture_coords, _tint_verts, _tri_faces


_unit_cube_attrs = _create_unit_cube_attrs()


def get_unit_cube(
        down: str,
        up: str,
        north: str,
        east: str,
        south: str,
        west: str,
        transparency=0
) -> BlockMesh:
    _verts, _texture_coords, _tint_verts, _tri_faces = _unit_cube_attrs
    texture_paths, texture_index = numpy.unique((down, up, north, east, south, west), return_inverse=True)
    texture_paths = tuple(texture_paths)
    _tri_texture_index: Dict[str, numpy.ndarray] = {
        side: numpy.full(2, texture_index[side_index], dtype=numpy.uint32)
        for side_index, side in enumerate(cube_face_lut)
    }

    return BlockMesh(
        3,
        _verts,
        _texture_coords,
        _tint_verts,
        _tri_faces,
        _tri_texture_index,
        texture_paths,
        transparency,
    )



