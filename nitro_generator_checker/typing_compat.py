from __future__ import annotations

import sys

if sys.version_info >= (3, 12):
    from typing import Any, override
else:
    from typing_extensions import Any, override

__all__ = ("Any", "override")
