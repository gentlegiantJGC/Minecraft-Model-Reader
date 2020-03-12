from typing import Dict, Tuple, List, TYPE_CHECKING
import os
import copy
from minecraft_model_reader import MinecraftMesh

if TYPE_CHECKING:
	from amulet.api.block import Block

default_pack_icon = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'image', 'missing_pack_java.png')
missing_no = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'image', 'missing_no.png')

face_set = {'down', 'up', 'north', 'east', 'south', 'west', None}


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
		self._cached_models: Dict[Block, MinecraftMesh] = {}

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
