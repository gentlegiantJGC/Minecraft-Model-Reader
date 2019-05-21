import os
import re
from typing import List, Dict, Union
import comment_json
from api.block import Block


class MinecraftJavaModelHandler:
	properties_regex = re.compile(r"(?:,(?P<name>[a-z0-9_]+)=(?P<value>[a-z0-9_]+))")

	def __init__(self, asset_dirs: List[str]):
		self._models = {}
		self._asset_dirs = asset_dirs

	def reload_resources(self, asset_dirs: List[str]):
		self._models.clear()
		self._asset_dirs = asset_dirs

	def get_model(self, blockstate_str: str) -> dict:
		if blockstate_str not in self._models:
			self._models[blockstate_str] = self._parse_model(*Block.parse_blockstate_string(blockstate_str))
		return self._models[blockstate_str]

	@staticmethod
	def _missing_no():
		return {'missing':'no'}

	def _parse_model(self, namespace: str, base_name: str, properties: Dict[str, str]) -> dict:
		for asset_dir in reversed(self._asset_dirs):
			if namespace in os.listdir(asset_dir):
				if f'{base_name}.json' in os.listdir(os.path.join(asset_dir, namespace, 'blockstates')):
					try:
						blockstate = comment_json.from_file(os.path.join(asset_dir, namespace, 'blockstates', f'{base_name}.json'))
					except:
						continue

					if 'variants' in blockstate:
						for variant in blockstate['variants']:
							if variant == '':
								try:
									return self._load_block_model(namespace, blockstate['variants'][variant])
								except:
									pass
							else:
								properties_match = self.properties_regex.finditer(variant)
								if all(properties.get(match.group("name"), None) == match.group("value") for match in properties_match):
									try:
										return self._load_block_model(namespace, blockstate['variants'][variant])
									except:
										pass

					elif 'multipart' in blockstate:
						pass
						# TODO

		return self._missing_no()

	def _load_block_model(self, namespace: str, blockstate: Union[dict, list]) -> dict:
		if isinstance(blockstate, list):
			blockstate = blockstate[0]
		if 'model' not in blockstate:
			raise Exception
		model_path = blockstate['model']
		rotx = blockstate.get('x', 0)
		roty = blockstate.get('y', 0)
		# uvunlock = blockstate.get('uvunlock', False)

		return self._recursive_load_block_model(namespace, model_path)

	def _recursive_load_block_model(self, namespace: str, model_path: str) -> dict:
		asset_dir = next(asset_dir_ for asset_dir_ in self._asset_dirs if os.path.isfile(os.path.join(asset_dir_, namespace, 'models', f'{model_path}.json')))
		model = comment_json.from_file(os.path.join(asset_dir, namespace, 'models', f'{model_path}.json'))
		if 'parent' in model:
			parent_model = self._recursive_load_block_model(namespace, model['parent'])
		else:
			parent_model = {}
		if 'textures' in model:
			if 'textures' not in parent_model:
				parent_model['textures'] = {}
			for key, val in model['textures'].items():
				parent_model['textures'][key] = val
		if 'elements' in model:
			parent_model['elements'] = model['elements']

		return parent_model


if __name__ == '__main__':
	java_model_handler = MinecraftJavaModelHandler(['assets'])
	print(java_model_handler.get_model('minecraft:brown_carpet'))
