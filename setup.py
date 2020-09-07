import os
import os.path as op
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
        "minecraft_model_reader.*",
        "minecraft_model_reader.api.*",
        "minecraft_model_reader.java.*",
        "minecraft_model_reader.lib.*"
    ],
    exclude=[],
)

package_data_locations = (
    ("api", "image",),
    ("api", "resource_pack", "java", "resource_packs",)
)

package_data = []
for location_data_tuple in package_data_locations:
    location_files = []
    for root, _, filenames in os.walk(
        op.join(op.dirname(__file__), "minecraft_model_reader", *location_data_tuple)
    ):
        for filename in filenames:
            if "__pycache__" in root:
                continue
            location_files.append(op.join(root, filename))
    package_data.extend(location_files)

SETUP_PARAMS = {
    "name": "minecraft-model-reader",
    "install_requires": requirements,
    "packages": packages,
    "include_package_data": True,
    "zip_safe": False,
    "package_data": {"minecraft_model_reader": package_data},
}

setup(**SETUP_PARAMS)
