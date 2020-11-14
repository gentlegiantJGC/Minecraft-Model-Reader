import json
import os
import amulet_nbt

from minecraft_model_reader.api.resource_pack.bedrock.download_resources import (
    get_bedrock_vanilla_latest,
    get_bedrock_vanilla_fix,
)
from minecraft_model_reader.api.resource_pack import (
    load_resource_pack_manager,
    load_resource_pack,
)
from minecraft_model_reader.api import Block

ExtraRP = [
    r"C:\Program Files\WindowsApps\Microsoft.MinecraftUWP_1.16.2054.0_x64__8wekyb3d8bbwe\data\resource_packs\education",
    r"C:\Program Files\WindowsApps\Microsoft.MinecraftUWP_1.16.2054.0_x64__8wekyb3d8bbwe\data\resource_packs\chemistry",
]

NBTMap = {
    "byte": amulet_nbt.TAG_Byte,
    "int": amulet_nbt.TAG_Int,
    "string": amulet_nbt.TAG_String,
}


def main():
    rp_latest = get_bedrock_vanilla_latest()
    extra = [load_resource_pack(path) for path in ExtraRP if os.path.isdir(path)]
    rp_fix = get_bedrock_vanilla_fix()
    rp = load_resource_pack_manager([rp_latest, *extra, rp_fix])
    print(rp.pack_paths)
    with open(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "minecraft_model_reader",
            "api",
            "resource_pack",
            "bedrock",
            "block_palette.json",
        )
    ) as f:
        palette = json.load(f)
    missing = rp.missing_block
    for state in palette["blocks"]:
        namespace, basename = state["name"].split(":", 1)
        block = Block(
            namespace,
            basename,
            {
                prop["name"]: NBTMap[prop["type"]](prop["value"])
                for prop in state["states"]
            },
        )
        block_mesh = rp.get_block_model(block)
        if block_mesh == missing:
            print(f"{block} does not currently have a block model")


if __name__ == "__main__":
    main()
