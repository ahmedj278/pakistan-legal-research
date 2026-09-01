"""
Shared pytest fixtures/setup.

Stubs sentence_transformers and chromadb at import time ONLY if
they're not installed — most of this project's modules import them
transitively (via app.search/app.embeddings), but the logic under
test in these files (citations, query_processing, rag routing,
documents, evaluation) doesn't actually need real embeddings or a
real vector DB to be correct. If you DO have the full stack
installed (as the actual running app requires), these stubs are
skipped and the real packages are used — this only helps a reviewer
run the test suite without installing the heavy ML dependencies
first.
"""

import sys
from unittest.mock import MagicMock

for _module in ("sentence_transformers", "chromadb"):
    try:
        __import__(_module)
    except ImportError:
        sys.modules[_module] = MagicMock()
