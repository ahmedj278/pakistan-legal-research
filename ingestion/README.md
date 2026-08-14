# Ingestion

Turns raw Pakistani court judgment PDFs into structured, extracted
text ready for later processing (cleaning, metadata extraction,
chunking — Sessions 2.3+).

**Status:** Discovery + text extraction implemented (Module 2,
Sessions 2.1–2.2).

**Scope:** Supreme Court and Islamabad High Court only, for now.
Balochistan HC and Peshawar HC (whose judgments are merged into
multi-case "volume" PDFs) are intentionally out of scope — see
`docs/` for reasoning. This is a deliberate, documented limitation,
not an oversight.

## Structure

```text
ingestion/
├── requirements.txt
├── src/
│   ├── config.py          source directories, output paths, thresholds
│   ├── models.py           RawDocument data structure
│   ├── logger.py           shared structured logging setup
│   ├── discovery.py        finds PDF files (Session 2.1)
│   ├── extraction.py       extracts text from each PDF (Session 2.2)
│   └── run_ingestion.py    entry point — runs discovery + extraction
├── data/
│   ├── raw/                 put/point your PDFs here (gitignored)
│   │   ├── supreme_court/
│   │   └── islamabad_high_court/
│   └── processed/            output JSON lands here (gitignored)
└── logs/                     one timestamped log file per run (gitignored)
```

## Setup

```bash
cd ingestion
python -m venv venv          # Windows: py -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configure where your PDFs actually live

By default, the pipeline looks in `ingestion/data/raw/supreme_court/`
and `ingestion/data/raw/islamabad_high_court/`. Since your real PDF
collection almost certainly lives elsewhere (and you won't want to
copy thousands of files into the repo folder), point at your real
folders instead by setting these in your root `.env`:

```bash
INGESTION_SC_DIR=C:/path/to/your/supreme-court-pdfs
INGESTION_IHC_DIR=C:/path/to/your/ihc-pdfs
```

## Run

```bash
cd ingestion/src
python run_ingestion.py       # Windows: py run_ingestion.py
```

For now, **test against a small sample first** (e.g. the ~50 PDFs
per court you mentioned) before pointing it at the full collection —
partly to sanity-check the output, partly because a full run over
thousands of PDFs will take a while and you'll want to review a
summary run first.

## What it does

For every PDF found in each configured court folder:
1. Opens it and extracts text, page by page.
2. Writes one JSON file to `data/processed/<court>/<filename>.pdf.json`
   containing the raw text plus metadata about the extraction itself
   (page count, character count, status).
3. Never crashes the whole run over one bad file — failures are
   caught, logged with the filename, and the file is marked
   `failed` (with the error message) or `empty_text` (fewer than 50
   characters extracted — almost always means it's a scanned image
   with no real text layer) so you can review problem files
   afterward instead of the run silently dying partway through
   thousands of PDFs.
4. Prints/logs a summary: how many succeeded, how many were flagged,
   how many failed.

## Why no OCR yet

Both real sample PDFs (one Supreme Court judgment, one IHC order
sheet) extracted cleanly with a real text layer — no OCR needed. If,
after running this against your full sample, a meaningful number of
files come back `empty_text`, that's the signal OCR needs to be
added as a later stage. Not building it preemptively for files that
may not need it.

## Example output

```json
{
  "source_path": "/path/to/1786541116727_c_a__3_l_2016.pdf",
  "filename": "1786541116727_c_a__3_l_2016.pdf",
  "court": "supreme_court",
  "size_bytes": 84213,
  "page_count": 6,
  "raw_text": "IN THE SUPREME COURT OF PAKISTAN\n(Appellate Jurisdiction)\n...",
  "char_count": 12964,
  "extraction_status": "ok",
  "extraction_error": null
}
```
