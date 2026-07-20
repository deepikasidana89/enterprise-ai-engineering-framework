"""EARF - Enterprise AI Readiness Framework (Phase 1 skeleton)
"""
from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__"]

try:
    __version__ = version("earf")
except PackageNotFoundError:
    __version__ = "0.1.0-dev"
