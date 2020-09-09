import itertools
import numpy
from typing import Dict, Union, TYPE_CHECKING

from .block_mesh import BlockMesh
from .cube import cube_face_lut as _cube_face_lut, tri_face as _tri_face

if TYPE_CHECKING:
    from minecraft_model_reader.api.resource_pack.base import BaseResourcePackManager


_box_coordinates = numpy.array(list(itertools.product([0, 1], [0, 1], [0, 1])))

_texture_uv = numpy.array([0, 0, 1, 1], numpy.float)
_uv_slice = [0, 1, 2, 1, 2, 3, 0, 3]

_verts: Dict[Union[str, None], numpy.ndarray] = {}
_texture_coords = {}
_tint_verts = {}
_tri_faces = {}
_tri_texture_index: Dict[Union[str, None], numpy.ndarray] = {
    side: numpy.zeros(2, dtype=numpy.uint32)
    for side in ("down", "up", "north", "east", "south", "west")
}

for _face_dir in _cube_face_lut:
    _verts[_face_dir] = _box_coordinates[
        _cube_face_lut[_face_dir]
    ].ravel()  # vertex coordinates for this face
    _texture_coords[_face_dir] = _texture_uv[_uv_slice]  # texture vertices
    _tint_verts[_face_dir] = numpy.ones(12, dtype=numpy.float)
    _tri_faces[_face_dir] = _tri_face


def get_missing_block(resource_pack: "BaseResourcePackManager") -> BlockMesh:
    texture_path = resource_pack.get_texture("minecraft", "missing_no")
    return BlockMesh(
        3,
        _verts,
        _texture_coords,
        _tint_verts,
        _tri_faces,
        _tri_texture_index,
        (texture_path, ),
        0,
    )
