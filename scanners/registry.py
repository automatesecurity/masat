"""Scanner registry and discovery.

This enables a lightweight plugin architecture: any module in `scanners/` that
exposes a coroutine named `scan(target, verbose=False)` can be discovered.

Optional module attributes:
- SCAN_ID: stable identifier (default: module name)
- DESCRIPTION: human-readable description
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from types import ModuleType
from typing import Callable, Awaitable


@dataclass(frozen=True)
class ScannerSpec:
    scan_id: str
    description: str
    module: ModuleType

    @property
    def scan(self) -> Callable[..., Awaitable[dict]]:
        return getattr(self.module, "scan")


def discover_scanners() -> dict[str, ScannerSpec]:
    """Discover scanner modules under the `scanners` package."""
    import scanners  # local package

    specs: dict[str, ScannerSpec] = {}
    for modinfo in pkgutil.iter_modules(scanners.__path__, scanners.__name__ + "."):
        if modinfo.name.endswith(".registry"):
            continue

        module = importlib.import_module(modinfo.name)

        scan_fn = getattr(module, "scan", None)
        if scan_fn is None:
            continue

        scan_id = getattr(module, "SCAN_ID", modinfo.name.split(".")[-1])
        description = getattr(module, "DESCRIPTION", "")

        specs[scan_id] = ScannerSpec(scan_id=scan_id, description=description, module=module)

    return dict(sorted(specs.items(), key=lambda kv: kv[0]))
