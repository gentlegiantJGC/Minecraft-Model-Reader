import json
import os

colours = ("red", "green", "cyan", "orange", "light_gray", "brown", "pink", "light_blue", "magenta", "white", "purple", "blue", "yellow", "gray", "lime", "black")
rotations = {"north": 0, "east": 90, "south": 180, "west": 270}
parts = ("foot", "head")

os.makedirs("./../models/block/bed", exist_ok=True)
for colour in colours:
    blockstate_file = {
        f"part={part},facing={facing}": {"model": f"block/bed/{colour}_{part}", "y": rotation} if rotation else {"model": f"block/bed/{colour}_{part}"} for part in parts for facing, rotation in rotations.items()
    }
    with open(f"{colour}_bed.json", 'w') as f:
        json.dump(
            {
                "variants": blockstate_file
            },
            f,
            indent='\t'
        )

    for part in parts:
        with open(f"./../models/block/bed/{colour}_{part}.json", 'w') as f:
            json.dump(
                {
                    "parent": f"block/bed_{part}",
                    "textures": {
                        "all": f"entity/bed/{colour}"
                    }
                },
                f,
                indent='\t'
            )
