import os
import json
import copy
from typing import List, Union, Dict, Tuple
from .api import base_api
try:
	from amulet.api.block import Block
except:
	from .api.block import Block
from . import java_block_model


class JavaRP(base_api.BaseRP):
	"""A class to hold the bare bones information about the resource pack.
	Holds the pack format, description and if the pack is valid.
	This information can be used in a viewer to display the packs to the user."""
	def __init__(self, resource_pack_path: str):
		base_api.BaseRP.__init__(self)
		assert os.path.isdir(resource_pack_path), 'The given path must be a directory'
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
	"""A class to load and handle the data from the packs.
	Packs are given as a list with the later packs overwriting the earlier ones."""
	def __init__(self, resource_packs: Union[JavaRP, List[JavaRP]]):
		base_api.BaseRPHandler.__init__(self)
		if isinstance(resource_packs, list) and all(isinstance(path, JavaRP) for path in resource_packs):
			self._packs = resource_packs
		elif isinstance(resource_packs, JavaRP):
			self._packs = [resource_packs]
		self.reload()

	def reload(self):
		"""Reload the resources from the resource packs.
		This clears all memory and repopulates it."""
		self.unload()

		blockstate_file_paths: Dict[Tuple[str, str], str] = {}
		model_file_paths: Dict[Tuple[str, str], str] = {}

		for pack in self._packs:
			# pack_format=2 textures/blocks, textures/items - case sensitive
			# pack_format=3 textures/blocks, textures/items - lower case
			# pack_format=4 textures/block, textures/item

			if pack.valid_pack and os.path.isdir(os.path.join(pack.root_dir, 'assets')):
				for namespace in os.listdir(os.path.join(pack.root_dir, 'assets')):
					if os.path.isdir(os.path.join(pack.root_dir, 'assets', namespace)):
						if pack.pack_format >= 2:
							if os.path.isdir(os.path.join(pack.root_dir, 'assets', namespace, 'textures')):
								for root, _, files in os.walk(os.path.join(pack.root_dir, 'assets', namespace, 'textures')):
									for f in files:
										if f.endswith('.png'):
											rel_path = os.path.relpath(os.path.join(root, f[:-4]), os.path.join(pack.root_dir, 'assets', namespace, 'textures'))
										else:
											continue
										self._textures[(namespace, rel_path)] = os.path.join(root, f)

							if os.path.isdir(os.path.join(pack.root_dir, 'assets', namespace, 'blockstates')):
								for f in os.listdir(os.path.join(pack.root_dir, 'assets', namespace, 'blockstates')):
									if f.endswith('.json'):
										blockstate_file_paths[(namespace, f[:-5])] = os.path.join(pack.root_dir, 'assets', namespace, 'blockstates', f)

							if os.path.isdir(os.path.join(pack.root_dir, 'assets', namespace, 'models')):
								for root, _, files in os.walk(os.path.join(pack.root_dir, 'assets', namespace, 'models')):
									for f in files:
										if f.endswith('.json'):
											rel_path = os.path.relpath(os.path.join(root, f[:-5]), os.path.join(pack.root_dir, 'assets', namespace, 'models'))
											model_file_paths[(namespace, rel_path.replace(os.sep, '/'))] = os.path.join(root, f)

		for key, path in blockstate_file_paths.items():
			with open(path) as fi:
				self._blockstate_files[key] = json.load(fi)

		for key, path in model_file_paths.items():
			with open(path) as fi:
				self._model_files[key] = json.load(fi)

	def get_model(self, block: Block, face_mode: int = 3):
		# TODO: add some logic here to convert the block to Java blockstate format if it is not already
		if block.blockstate not in self._cached_models:
			self._cached_models[block.blockstate_without_waterlogged] = java_block_model.get_model(self, block, face_mode)
		return copy.deepcopy(self._cached_models[block.blockstate])
