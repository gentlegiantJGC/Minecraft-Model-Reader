import os
import json
from typing import List, Union
from .api import base_api


class JavaRP(base_api.BaseRP):
	"""
	A class to hold the bare bones information about the resource pack.
	Holds the pack format, description and if the pack is valid.
	This information can be used in a viewer to display the packs to the user.
	"""
	def __init__(self, resource_pack_path: str):
		base_api.BaseRP.__init__(self)
		self._root_dir = resource_pack_path
		try:
			if os.path.isfile(os.path.join(resource_pack_path, 'pack.mcmeta')):
				with open(os.path.join(resource_pack_path, 'pack.mcmeta')) as f:
					pack_mcmeta = json.load(f)
				self._pack_format = pack_mcmeta['pack']['pack_format']
				self._pack_description = str(pack_mcmeta['pack'].get('description', ''))
				self._valid_pack = True
		except:
			pass

		if self._valid_pack:
			if os.path.isfile(os.path.join(resource_pack_path, 'pack.png')):
				self._pack_icon = os.path.join(resource_pack_path, 'pack.png')


class JavaRPHandler(base_api.BaseRPHandler):
	"""
	A class to load and handle the data from the packs.
	Packs are given as a list with the later packs overwriting the earlier ones.
	"""
	def __init__(self, resource_packs: Union[JavaRP, List[JavaRP]]):
		base_api.BaseRPHandler.__init__(self)
		if isinstance(resource_packs, list) and all(isinstance(path, JavaRP) for path in resource_packs):
			self._packs = resource_packs
		elif isinstance(resource_packs, JavaRP):
			self._packs = [resource_packs]

	def reload(self):
		self.unload()

		for pack in self._packs:

			"""
			pack_format=2 textures/blocks, textures/items - case sensitive
			pack_format=3 textures/blocks, textures/items - lower case
			pack_format=4 textures/block, textures/item
			"""

			if pack.valid_pack and os.path.isdir(os.path.join(pack.root_dir, 'assets')):
				for namespace in os.listdir(os.path.join(pack.root_dir, 'assets')):
					if pack.pack_format >= 2:

						if os.path.isdir(os.path.join(pack.root_dir, 'assets', namespace, 'textures')):
							for root, _, files in os.walk(os.path.join(pack.root_dir, 'assets', namespace, 'textures')):
								for f in files:
									rel_path = os.path.relpath(os.path.join(root, f), os.path.join(pack.root_dir, 'assets', namespace, 'textures'))
									if pack.pack_format >= 3:
										rel_path = rel_path.lower()
									self._textures[rel_path] = os.path.join(root, f)

	def unload(self):
		self._textures.clear()
