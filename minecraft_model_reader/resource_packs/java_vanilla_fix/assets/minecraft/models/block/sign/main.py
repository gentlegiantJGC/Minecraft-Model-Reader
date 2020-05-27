import os
import json

for material in os.listdir(r"D:\Data\GitHub\Minecraft-Model-Reader\minecraft_model_reader\resource_packs\java_vanilla\assets\minecraft\textures\entity\signs"):
    material = material[:-4]
    for rotation in range(4):
        with open(f"{material}_{rotation}.json", 'w') as f:
            json.dump(
                {
                    "parent": f"block/sign/sign_{rotation}",
                    "textures": {
                        "all": f"entity/signs/{material}",
                        "particle": f"block/{material}_planks"
                    }
                },
                f,
                indent='\t'
            )
