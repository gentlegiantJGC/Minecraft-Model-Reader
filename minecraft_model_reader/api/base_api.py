from typing import Dict
import os

default_pack_icon = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'image', 'missing_pack_java.png')
missing_no = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'image', 'missing_no.png')


class BaseRP:
	"""
	The base class that all resource packs must inherit from. Defines the base api.
	"""
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
	"""
	The base class that all resource pack handlers must inherit from. Defines the base api.
	"""
	def __init__(self):
		self._packs = []
		self._textures = {}
		self._missing_no = missing_no

	def get_texture(self, path: str):
		if path in self._textures:
			return self._textures[path]
		else:
			return self._missing_no
