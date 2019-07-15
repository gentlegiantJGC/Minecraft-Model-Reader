import minecraft_model_reader
try:
	from amulet.api.block import Block
except:
	from minecraft_model_reader.api.block import Block

vanilla_1_13_2 = minecraft_model_reader.JavaRP('./../test_packs/Vanilla 1.13.2')

resource_pack = minecraft_model_reader.JavaRPHandler([vanilla_1_13_2])

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

air_model = resource_pack.get_model(air)
stone_model = resource_pack.get_model(stone)
fire_model = resource_pack.get_model(fire)

print('Read successfully')
