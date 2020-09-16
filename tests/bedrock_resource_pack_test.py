import json
import os
import amulet_nbt

from minecraft_model_reader.api.resource_pack.bedrock.download_resources import get_bedrock_vanilla_latest, get_bedrock_vanilla_fix
from minecraft_model_reader.api.resource_pack import load_resource_pack_manager
from minecraft_model_reader.api import Block

NBTMap = {
    "byte": amulet_nbt.TAG_Byte,
    "int": amulet_nbt.TAG_Int,
    "string": amulet_nbt.TAG_String
}


def main():
    rp_latest = get_bedrock_vanilla_latest()
    rp_fix = get_bedrock_vanilla_fix()
    rp = load_resource_pack_manager([rp_latest, rp_fix])
    with open(os.path.join(os.path.dirname(__file__), "..", "minecraft_model_reader", "api", "resource_pack", "bedrock", "block_palette.json")) as f:
        palette = json.load(f)
    missing = rp.missing_block
    for state in palette["blocks"]:
        namespace, basename = state["name"].split(":", 1)
        block = Block(
            namespace,
            basename,
            {
                prop["name"]: NBTMap[prop["type"]](prop["value"]) for prop in state["states"]
            }
        )
        block_mesh = rp.get_block_model(block)
        if block_mesh == missing:
            print(f"{block} does not currently have a block model")


if __name__ == '__main__':
    main()
