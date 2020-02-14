from typing import Dict, Tuple, List, Union, TYPE_CHECKING
import os
import copy
import numpy

if TYPE_CHECKING:
	from amulet.api.block import Block

default_pack_icon = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'image', 'missing_pack_java.png')
missing_no = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'image', 'missing_no.png')

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
		is_opaque: bool
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
		:param is_opaque: is the model a full non-transparent block

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
			key in face_set and isinstance(val, numpy.ndarray) and val.ndim == 1 for key, val in tint_verts.items()
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
		self._is_opaque = is_opaque

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
		The tint table is a flat numpy bool array with one value per vertex.
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
		return self._is_opaque


class BaseRP:
	"""The base class that all resource packs must inherit from. Defines the base api."""
	def __init__(self):
		self._valid_pack = False
		self._root_dir = None
		self._pack_format = None
		self._pack_description = ''
		self._pack_icon = default_pack_icon

	@property
	def valid_pack(self) -> bool:
		"""bool - does the pack meet the minimum requirements to be a resource pack"""
		return self._valid_pack

	@property
	def root_dir(self) -> str:
		"""str - the root directory of the pack"""
		return self._root_dir

	@property
	def pack_format(self) -> int:
		"""int - pack format number"""
		return self._pack_format

	@property
	def pack_description(self) -> str:
		"""str - the description as described in the pack"""
		return self._pack_description

	@property
	def pack_icon(self) -> str:
		"""str - path to the pack icon"""
		return self._pack_icon


class BaseRPHandler:
	"""The base class that all resource pack handlers must inherit from. Defines the base api."""
	def __init__(self):
		self._packs: List[BaseRP] = []
		self._missing_no = missing_no
		self._textures: Dict[Tuple[str, str], str] = {}
		self._texture_is_transparrent: Dict[str, List[int, bool]] = {}
		self._blockstate_files: Dict[Tuple[str, str], dict] = {}
		self._model_files: Dict[Tuple[str, str], dict] = {}
		self._cached_models = {}

	@property
	def pack_paths(self):
		return [pack.root_dir for pack in self._packs]

	def unload(self):
		"""Clear all loaded resources."""
		self._textures.clear()
		self._blockstate_files.clear()
		self._model_files.clear()
		self._cached_models.clear()

	@property
	def missing_no(self) -> str:
		"""The path to the missing_no image"""
		return self._missing_no

	@property
	def textures(self) -> Dict[Tuple[str, str], str]:
		"""Returns a deepcopy of self._textures.
		Keys are a tuple of (namespace, relative paths used in models)
		Values are the absolute path to the texture"""
		return copy.deepcopy(self._textures)

	@property
	def blockstate_files(self) -> Dict[Tuple[str, str], dict]:
		"""Returns self._blockstate_files.
		Keys are a tuple of (namespace, relative paths used in models)
		Values are the blockstate files themselves (should be a dictionary)"""
		return self._blockstate_files

	@property
	def model_files(self) -> Dict[Tuple[str, str], dict]:
		"""Returns self._model_files.
		Keys are a tuple of (namespace, relative paths used in models)
		Values are the model files themselves (should be a dictionary or MinecraftMesh)"""
		return self._model_files

	def get_texture(self, namespace_and_path: Tuple[str, str]) -> str:
		"""Get the absolute texture path from the namespace and relative path pair"""
		if namespace_and_path in self._textures:
			return self._textures[namespace_and_path]
		else:
			return self._missing_no

	def get_model(self, block: 'Block'):
		raise NotImplemented
