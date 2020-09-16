import importlib.util
import os

__all__ = [
    module[:-3]
    for module in os.listdir(os.path.dirname(__file__))
    if module.endswith(".py") and module != "__init__.py"
]

from .base_blockshape import BaseBlockShape

BlockShapeClasses = {}
_class_names = set()

for module in __all__:
    module_path = os.path.join(os.path.dirname(__file__), module + ".py")
    spec = importlib.util.spec_from_file_location(
        os.path.basename(module_path), module_path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if hasattr(mod, "BlockShape"):
        blockshape = getattr(mod, "BlockShape")
        if isinstance(blockshape, BaseBlockShape):
            if blockshape.blockshape in BlockShapeClasses:
                print(f"Name conflict with blockshape {blockshape.blockshape}")
            if blockshape.__class__.__name__ in _class_names:
                print(f"Duplicate class name {blockshape.__class__.__name__}")
            else:
                _class_names.add(blockshape.__class__.__name__)
            BlockShapeClasses[blockshape.blockshape] = blockshape
