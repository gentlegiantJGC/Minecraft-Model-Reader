from typing import Dict, Tuple, List, Union
import numpy

face_set = {'down', 'up', 'north', 'east', 'south', 'west', None}


class MinecraftMesh:
    """Class for storing model data"""
    def __init__(
        self,
        face_width: int,
        verts: Dict[Union[str, None], numpy.ndarray],
        texture_coords: Dict[Union[str, None], numpy.ndarray],
        tint_verts: Dict[Union[str, None], numpy.ndarray],
        # normals: Dict[Union[str, None], numpy.ndarray],
        faces: Dict[Union[str, None], numpy.ndarray],
        texture_index: Dict[Union[str, None], numpy.ndarray],
        textures: List[Tuple[str, Union[None, str]]],
        transparency: int
    ):
        """

        :param face_width: the number of vertices per face (3 or 4)
        :param verts: a numpy float array containing the vert data. One line per vertex
        :param texture_coords: a numpy float array containing the texture coordinate data. One line per vertex
        :param tint_verts: a numpy bool array if the vertex should have a tint applied to it. One line per vertex
        :param faces: a dictionary of numpy int arrays (stored under cull direction) containing
            the vertex indexes (<face_width> columns) and
            texture index (1 column)
        :param texture_index:
        :param textures:
        :param transparency: is the model a full non-transparent block

        Workflow:
            find the directions a block is not being culled in
            look them up in the face table
            the face table will tell you which vertices are needed for the face
        """
        assert isinstance(verts, dict) and all(
            key in face_set and isinstance(val, numpy.ndarray) and val.ndim == 1 and val.shape[0] % 3 == 0 for key, val in verts.items()
        ), 'The format for verts is incorrect'

        assert isinstance(texture_coords, dict) and all(
            key in face_set and isinstance(val, numpy.ndarray) and val.ndim == 1 and val.shape[0] % 2 == 0 for key, val in texture_coords.items()
        ), 'The format for texture coords is incorrect'

        assert isinstance(tint_verts, dict) and all(
            key in face_set and isinstance(val, numpy.ndarray) and val.ndim == 1 and val.shape[0] % 3 == 0 for key, val in tint_verts.items()
        ), 'The format of tint verts is incorrect'

        assert isinstance(faces, dict) and all(
            key in face_set and isinstance(val, numpy.ndarray) and numpy.issubdtype(val.dtype, numpy.unsignedinteger) and val.ndim == 1 and val.shape[0] % face_width == 0 for key, val in faces.items()
        ), 'The format of faces is incorrect'

        assert isinstance(texture_index, dict) and all(
            key in face_set and isinstance(val, numpy.ndarray) and numpy.issubdtype(val.dtype, numpy.unsignedinteger) and val.ndim == 1 and val.shape[0] == faces[key].shape[0] / face_width for key, val in texture_index.items()
        ), 'The format of texture index is incorrect'

        assert isinstance(textures, list) and all(
            isinstance(texture, tuple) and len(texture) == 2 and isinstance(texture[0], str) and (isinstance(texture[1], str) or texture[1] is None) for texture in textures
        ), 'The format of the textures is incorrect'

        self._face_mode = face_width
        self._verts = verts
        self._texture_coords = texture_coords
        self._tint_verts = tint_verts
        self._vert_tables = None

        self._faces = faces
        self._texture_index = texture_index
        self._textures = textures
        self._transparency = transparency

        [a.setflags(write=False) for a in self._verts.values()]
        [a.setflags(write=False) for a in self._texture_coords.values()]
        [a.setflags(write=False) for a in self._faces.values()]
        [a.setflags(write=False) for a in self._texture_index.values()]

    @property
    def face_mode(self) -> int:
        """The number of vertices per face"""
        return self._face_mode

    @property
    def vert_tables(self) -> Dict[str, numpy.ndarray]:
        """A dictionary of cull dir -> the flat vert table containing vertices, texture coords and (in the future) normals"""
        if self._vert_tables is None:
            self._vert_tables = {
                key: numpy.hstack((
                    self._verts[key].reshape(-1, self._face_mode),
                    self._texture_coords[key].reshape(-1, 2)
                    # TODO: add in face normals
                )).ravel()
                for key in self._verts.keys()
            }
            [a.setflags(write=False) for a in self._vert_tables.values()]
        return self._vert_tables

    @property
    def verts(self) -> Dict[str, numpy.ndarray]:
        """A dictionary mapping face cull direction to the vertex table for that direction.
        The vertex table is a flat numpy array who's length is a multiple of 3.
        x,y,z coordinates."""
        return self._verts

    @property
    def texture_coords(self) -> Dict[str, numpy.ndarray]:
        """A dictionary mapping face cull direction to the texture coords table for that direction.
        The texture coords table is a flat numpy array who's length is a multiple of 2.
        tx, ty"""
        return self._texture_coords

    @property
    def tint_verts(self) -> Dict[str, numpy.ndarray]:
        """A dictionary mapping face cull direction to the tint table for that direction.
        The tint table is a flat numpy bool array with three values per vertex.
        """
        return self._tint_verts

    @property
    def faces(self) -> Dict[str, numpy.ndarray]:
        """A dictionary mapping face cull direction to the face table for that direction.
        The face table is a flat numpy array of multiple 3 or 4 depending on face_mode.
        First 3 or 4 columns index into the verts table.
        Last column indexes into textures."""
        return self._faces

    @property
    def texture_index(self) -> Dict[str, numpy.ndarray]:
        """A dictionary mapping face cull direction to the face table for that direction.
        The face table is a flat numpy array of multiple 2 indexing into textures."""
        return self._texture_index

    @property
    def textures(self) -> List[Tuple[str, Union[None, str]]]:
        """A list of all the texture paths."""
        return self._textures

    @property
    def is_opaque(self) -> bool:
        """
        If the model covers all surrounding blocks.
        Also takes into account texture transparency.
        """
        return not self._transparency

    @property
    def is_transparent(self) -> int:
        """
        The transparency mode of the block
        0 - the block is a full block with opaque textures
        1 - the block is a full block with transparent/translucent textures
        2 - the block is not a full block
        """
        return self._transparency
