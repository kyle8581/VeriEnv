from __future__ import annotations

import logging
import sys


def configure_logging() -> None:
    """
    Minimal structured-ish logging suitable for local/dev.
    (In prod you’d typically ship JSON logs; keeping it simple here.)
    """
    root = logging.getLogger()
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(logging.INFO)

