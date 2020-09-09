import minecraft_model_reader
from minecraft_model_reader.api import Block
from minecraft_model_reader.api.resource_pack.java import JavaResourcePack, JavaResourcePackManager

vanilla_1_13_2 = JavaResourcePack('./../test_packs/Vanilla 1.13.2')

resource_pack = JavaResourcePackManager([vanilla_1_13_2])

air: Block = Block(namespace='minecraft', base_name='air')
stone: Block = Block(namespace='minecraft', base_name='stone')
fire: Block = Block(namespace='minecraft', base_name='fire',
	properties={
		"age": "0",
		"east": "true",
		"north": "true",
		"south": "false",
		"up": "false",
		"west": "false"
	}
)

air_model = resource_pack.get_block_model(air)
stone_model = resource_pack.get_block_model(stone)
fire_model = resource_pack.get_block_model(fire)

print('Read successfully')
