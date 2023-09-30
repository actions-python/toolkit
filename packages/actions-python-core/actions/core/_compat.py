import sys

if sys.version_info < (3, 11):
    from typing_extensions import Self, Unpack
else:
    from typing import (
        Self,  # noqa: F401
        Unpack,  # noqa: F401
    )
