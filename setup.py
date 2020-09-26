import os
import os.path as op
from setuptools import setup, find_packages


with open("requirements.txt") as requirements_fp:
    requirements = [
        line for line in requirements_fp.readlines() if not line.startswith("git+")
    ]

packages = find_packages(include=["minecraft_model_reader", "minecraft_model_reader.*"])

package_data_locations = (("api", "image",), ("api", "resource_pack",))

package_data = []
for location_data_tuple in package_data_locations:
    for root, _, filenames in os.walk(
        op.join(op.dirname(__file__), "minecraft_model_reader", *location_data_tuple)
    ):
        for filename in filenames:
            if "__pycache__" in root or filename.endswith(".py"):
                continue
            package_data.append(op.join(root, filename))

SETUP_PARAMS = {
    "name": "minecraft-model-reader",
    "install_requires": requirements,
    "packages": packages,
    "include_package_data": True,
    "zip_safe": False,
    "package_data": {"minecraft_model_reader": package_data},
}

setup(**SETUP_PARAMS)
