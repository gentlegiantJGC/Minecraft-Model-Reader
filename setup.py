from setuptools import setup, find_packages
import os
import glob
import shutil
import versioneer

# there were issues with other builds carrying over their cache
for d in glob.glob("*.egg-info"):
    shutil.rmtree(d)


def remove_git_and_http_package_links(uris):
    for uri in uris:
        if uri.startswith("git+") or uri.startswith("https:"):
            continue
        yield uri


with open("./requirements.txt") as requirements_fp:
    required_packages = [
        line for line in remove_git_and_http_package_links(requirements_fp.readlines())
    ]

package_data = [
    os.path.relpath(path, "minecraft_model_reader") for path in
    set(
        glob.glob(
            os.path.join(
                "minecraft_model_reader",
                "**",
                "*.*"
            ),
            recursive=True
        )
    ) - set(
        glob.glob(
            os.path.join(
                "minecraft_model_reader",
                "**",
                "*.py[cod]"
            ),
            recursive=True
        )
    ) - set(
        glob.glob(
            os.path.join(
                "minecraft_model_reader",
                "api",
                "resource_pack",
                "bedrock",
                "resource_packs",
                "bedrock_vanilla",
                "**",
                "*.*"
            ),
            recursive=True
        )
    ) - set(
        glob.glob(
            os.path.join(
                "minecraft_model_reader",
                "api",
                "resource_pack",
                "java",
                "resource_packs",
                "java_vanilla",
                "**",
                "*.*"
            ),
            recursive=True
        )
    )
]

setup(
    name="minecraft-resource-pack",
    version=versioneer.get_version(),
    description="A Python library reading Minecraft's various resource pack formats.",
    author="James Clare",
    author_email="amuleteditor@gmail.com",
    install_requires=required_packages,
    packages=find_packages(),
    package_data={"minecraft_model_reader": package_data},
    cmdclass=versioneer.get_cmdclass(),
    setup_requires=required_packages,
    dependency_links=[
        "https://pypi.org/project/Pillow/",
        "https://pypi.org/project/numpy/",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
