import minecraft_model_reader

vanilla_1_13_2 = minecraft_model_reader.JavaRP('./../test_packs/Vanilla 1.13.2')

resource_pack = minecraft_model_reader.JavaRPHandler([vanilla_1_13_2])

print(resource_pack)