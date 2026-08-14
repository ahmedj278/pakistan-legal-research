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

    # -- set during metadata extraction (Session 2.4) --
    court_name: Optional[str] = None  # human-readable, e.g. "Supreme Court of Pakistan"
    case_title: Optional[str] = None
    judges: Optional[list] = None
    case_number: Optional[str] = None
    year: Optional[int] = None
    jurisdiction: Optional[str] = None
    hearing_date: Optional[str] = None
    decision_date: Optional[str] = None
    document_type: Optional[str] = None  # JUDGMENT | ORDER_SHEET | UNKNOWN
    citation: Optional[str] = None  # rarely present in the judgment text itself
    metadata_status: str = "pending"  # pending | ok | partial | skipped

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Chunk:
    # Every chunk carries the parent document's key metadata directly,
    # rather than just an ID to look up later — this is what lets a
    # RAG answer cite "which case, which court, which year" straight
    # from the retrieved chunk itself (see Module 5 requirements),
    # without a second lookup back to the source document.
    chunk_id: str
    chunk_index: int
    text: str
    char_count: int

    source_filename: str
    court: str
    court_name: Optional[str] = None
    case_title: Optional[str] = None
    case_number: Optional[str] = None
    year: Optional[int] = None
    judges: Optional[list] = None
    document_type: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
