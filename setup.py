import os
import os.path as op
import glob
from setuptools import setup, find_packages

CYTHON_COMPILE = False
try:
    from Cython.Build import cythonize

    CYTHON_COMPILE = True
except Exception:
    pass

requirements_fp = open(os.path.join(".", "requirements.txt"))
requirements = [
    line for line in requirements_fp.readlines() if not line.startswith("git+")
]
requirements_fp.close()

packages = find_packages(
    include=[
        "*",
    ],
    exclude=[],
)

package_data_locations = (
    ("api", "image",),
    ("api", "resource_pack", "java", "resource_packs",),
    ("api", "resource_pack", "bedrock", "resource_packs",),
    ("api", "resource_pack", "bedrock", "block_palette.json",),
    ("api", "resource_pack", "bedrock", "blockshapes.json",),
)

package_data = []
for location_data_tuple in package_data_locations:
    path = os.path.join(
            op.dirname(__file__),
            "minecraft_model_reader",
            *location_data_tuple
        )
    if os.path.isdir(path):
        for fpath in glob.iglob(
            os.path.join(path, "**", "*.*"), recursive=True
        ):
            if "__pycache__" in fpath or fpath.endswith(".py"):
                continue
            package_data.append(fpath)
    elif os.path.isfile(path):
        package_data.append(path)

SETUP_PARAMS = {
    "name": "minecraft-model-reader",
    "install_requires": requirements,
    "packages": packages,
    "include_package_data": True,
    "zip_safe": False,
    "package_data": {"minecraft_model_reader": package_data},
}

setup(**SETUP_PARAMS)
