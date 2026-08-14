"""
Shared data structure passed between ingestion stages.

Using a dataclass instead of a raw dict gives us autocomplete/type
hints as the pipeline grows through later sessions (cleaning,
metadata extraction, chunking), and one obvious place to see every
field a "document" carries at this stage.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class RawDocument:
    # -- set during discovery (Session 2.1) --
    source_path: str
    filename: str
    court: str  # derived from which source folder it came from
    size_bytes: int

    # -- set during extraction (Session 2.2) --
    page_count: Optional[int] = None
    raw_text: Optional[str] = None
    char_count: Optional[int] = None
    extraction_status: str = "pending"  # pending | ok | empty_text | failed
    extraction_error: Optional[str] = None

    # -- set during cleaning (Session 2.3) --
    cleaned_text: Optional[str] = None
    cleaned_char_count: Optional[int] = None
    cleaning_status: str = "pending"  # pending | ok | skipped

    def to_dict(self) -> dict:
        return asdict(self)
