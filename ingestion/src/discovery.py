"""
PDF discovery (Module 2, Session 2.1).

Finds candidate PDF files in a court's source directory. Deliberately
does the minimum here: find files, do a cheap sanity check (non-zero
size), and produce a RawDocument per file. Anything that requires
actually opening the PDF (page count, text) belongs in extraction.py
instead — keeping this stage fast and dependency-light.
"""

from pathlib import Path

from models import RawDocument


def discover_pdfs(directory: Path, court: str, logger) -> list[RawDocument]:
    if not directory.exists():
        logger.warning(f"Source directory does not exist, skipping: {directory}")
        return []

    documents = []
    all_files = sorted(directory.rglob("*"))

    for path in all_files:
        if not path.is_file():
            continue
        if path.suffix.lower() != ".pdf":
            logger.debug(f"Ignoring non-PDF file: {path.name}")
            continue

        size_bytes = path.stat().st_size
        if size_bytes == 0:
            logger.warning(f"Skipping zero-byte file: {path.name}")
            continue

        documents.append(
            RawDocument(
                source_path=str(path),
                filename=path.name,
                court=court,
                size_bytes=size_bytes,
            )
        )

    logger.info(f"[{court}] discovered {len(documents)} PDF(s) in {directory}")
    return documents
