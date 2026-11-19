import importlib
from pathlib import Path

_pkg_dir = Path(__file__).parent
for _f in _pkg_dir.glob("*.py"):
    if _f.stem.startswith("_"):
        continue
    importlib.import_module(f".{_f.stem}", __package__)
