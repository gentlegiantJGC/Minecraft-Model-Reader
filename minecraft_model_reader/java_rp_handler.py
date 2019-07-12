import os
import json
from typing import List, Union
from .api import base_api

default_pack_icon = None

class JavaRP(base_api.BaseRP):
	def __init__(self, resource_pack_path: str):
		BaseRP.__init__(self)
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

			for root, _, files in os.walk(self._root_dir):
				for f in files:
					self._files[os.path.relpath(os.path.join(root, f), self._root_dir)] = f

	def __iadd__(self, extend_resource_pack: 'JavaRP'):
		assert isinstance(extend_resource_pack, JavaRP), 'The extending instance must be a JavaRP instance'
		if extend_resource_pack.valid_pack and extend_resource_pack.pack_format == self.pack_format:
			for rel_path, abs_path in extend_resource_pack.files.items():
				self._files[rel_path] = abs_path
		# TODO: perhaps add some logging here to make the user aware a pack has failed to load
