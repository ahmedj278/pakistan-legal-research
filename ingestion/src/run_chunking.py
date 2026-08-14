"""
Main entry point for Module 2, Session 2.5 (chunking).

Usage:
    cd ingestion/src
    python run_chunking.py
    (Windows: py run_chunking.py)

Reads the JSON files run_metadata.py already enriched, chunks the
cleaned text, and writes one JSONL file per court to
data/chunks/<court>.jsonl — one line per chunk, each carrying its
parent document's key metadata directly (case title, court, case
number, year, judges, document type). This is the format Module 3
will read to generate embeddings.

JSONL (one JSON object per line) instead of one big JSON array:
standard for pipelines like this because it streams — a later stage
can process chunks one at a time without loading the whole court's
worth of chunks into memory at once.
"""

import json

from chunking import chunk_text
from config import OUTPUT_DIR, INGESTION_DIR
from logger import get_logger
from models import RawDocument, Chunk

CHUNKS_DIR = INGESTION_DIR / "data" / "chunks"


def build_chunks(doc: RawDocument) -> list:
    text_chunks = chunk_text(doc.cleaned_text)
    chunks = []
    for i, text in enumerate(text_chunks):
        chunks.append(
            Chunk(
                chunk_id=f"{doc.filename}::chunk_{i}",
                chunk_index=i,
                text=text,
                char_count=len(text),
                source_filename=doc.filename,
                court=doc.court,
                court_name=doc.court_name,
                case_title=doc.case_title,
                case_number=doc.case_number,
                year=doc.year,
                judges=doc.judges,
                document_type=doc.document_type,
            )
        )
    return chunks


def main():
    logger = get_logger("chunking")
    logger.info("Starting chunking run")
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    json_files = sorted(OUTPUT_DIR.rglob("*.json"))
    if not json_files:
        logger.warning(f"No processed JSON files found under {OUTPUT_DIR}")
        return

    # One output file handle per court, so chunks from documents
    # processed in any order still land in the right court's file.
    court_files = {}
    doc_count = 0
    chunk_count = 0
    skipped = 0

    try:
        for path in json_files:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            doc = RawDocument(**data)

            if doc.cleaning_status != "ok" or not doc.cleaned_text:
                skipped += 1
                continue

            chunks = build_chunks(doc)
            if not chunks:
                logger.warning(f"[{doc.court}] {doc.filename}: produced 0 chunks")
                skipped += 1
                continue

            if doc.court not in court_files:
                out_path = CHUNKS_DIR / f"{doc.court}.jsonl"
                court_files[doc.court] = open(out_path, "w", encoding="utf-8")

            for chunk in chunks:
                court_files[doc.court].write(
                    json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n"
                )

            doc_count += 1
            chunk_count += len(chunks)
            logger.info(f"[{doc.court}] {doc.filename}: {len(chunks)} chunk(s)")

    finally:
        for f in court_files.values():
            f.close()

    logger.info(
        f"Run complete — documents chunked: {doc_count}, total chunks: {chunk_count}, "
        f"documents skipped: {skipped}"
    )


if __name__ == "__main__":
    main()
