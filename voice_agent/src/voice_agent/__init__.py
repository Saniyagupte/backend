"""Voice agent package initializer.

Avoid importing heavy submodules (like `sst_engine`) at package import time
to keep lightweight scripts (e.g., the TTS demo) fast and dependency-free.
Submodules can be imported explicitly where needed.
"""

__all__ = []

