import importlib
import pkgutil
from typing import Dict
from patches.base import BasePatch

def discover_patches() -> Dict[str, BasePatch]:
    """Dynamically discover and instantiate all patch classes in the patches directory."""
    patches = {}
    package_path = __path__

    for _, module_name, is_pkg in pkgutil.iter_modules(package_path):
        if is_pkg or module_name == "base":
            continue
        
        module = importlib.import_module(f"patches.{module_name}")
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, BasePatch) and attr is not BasePatch:
                instance = attr()
                if instance.name:
                    patches[instance.name] = instance

    return patches
