from typing import Dict, Tuple, List, Union
import os
import copy
import numpy
try:
	from amulet.api.block import Block
except:
	from .block import Block

default_pack_icon = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'image', 'missing_pack_java.png')
missing_no = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'image', 'missing_no.png')

face_set = {'down', 'up', 'north', 'east', 'south', 'west', None}


class MinecraftMesh:
	"""Class for storing model data"""
	def __init__(self, verts: Dict[Union[str, None], numpy.ndarray], faces: Dict[Union[str, None], numpy.ndarray], textures: List[Tuple[str, Union[None, str]]]):
		assert isinstance(verts, dict) and all(
			key in face_set and isinstance(val, numpy.ndarray) and val.dtype == numpy.float and val.ndim == 2 and val.shape[1] == 5 for key, val in verts.items()
		), 'The format for verts is incorrect'

		face_width = set(val.shape[1] for val in faces.values())
		if len(face_width) == 0:
			face_width = {4}

		assert isinstance(faces, dict) and all(
			key in face_set and isinstance(val, numpy.ndarray) and val.dtype == numpy.uint32 and val.ndim == 2 and val.shape[1] in [4, 5] for key, val in faces.items()
		) and len(face_width) == 1, 'The format of faces is incorrect'

		assert isinstance(textures, list) and all(
			isinstance(texture, tuple) and len(texture) == 2 and isinstance(texture[0], str) and (isinstance(texture[1], str) or texture[1] is None) for texture in textures
		), 'The format of the textures is incorrect'

		self._face_mode = face_width.pop() - 1
		self._verts = verts
		self._faces = faces
		self._textures = textures

	@property
	def face_mode(self) -> int:
		return self._face_mode

	@property
	def verts(self) -> Dict[str, numpy.ndarray]:
		"""A dictionary mapping face cull direction to the vertex table for that direction.
		The vertex table is n n by 5 numpy array of vertex data.
		x,y,z coordinates in the first three columns.
		tx, ty in the last two columns"""
		return self._verts

	@property
	def faces(self) -> Dict[str, numpy.ndarray]:
		"""A dictionary mapping face cull direction to the face table for that direction.
		The face table is an N by 4 or 5 numpy array depending on face_mode.
		First 3 or 4 columns index into the verts table.
		Last column indexes into textures."""
		return self._faces

	@property
	def textures(self) -> List[Tuple[str, Union[None, str]]]:
		"""A list of all the texture paths."""
		return self._textures


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
		self._packs = []
		self._missing_no = missing_no
		self._textures: Dict[Tuple[str, str], str] = {}
		self._blockstate_files: Dict[Tuple[str, str], dict] = {}
		self._model_files: Dict[Tuple[str, str], dict] = {}
		self._cached_models = {}

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

	def get_model(self, block: Block):
		raise NotImplemented
