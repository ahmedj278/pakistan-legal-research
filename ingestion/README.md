# Ingestion

Turns raw Pakistani court judgment PDFs into structured, extracted
text ready for later processing (cleaning, metadata extraction,
chunking — Sessions 2.3+).

**Status:** Discovery, text extraction, cleaning, metadata
extraction, and chunking implemented (Module 2, Sessions 2.1–2.5).

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
│   ├── cleaning.py         cleans/normalizes extracted text (Session 2.3)
│   ├── metadata.py          per-court metadata extractors (Session 2.4)
│   ├── chunking.py          splits text into chunks (Session 2.5)
│   ├── run_ingestion.py    entry point — runs discovery + extraction
│   ├── run_cleaning.py      entry point — runs cleaning on already-extracted output
│   ├── run_metadata.py      entry point — runs metadata extraction on cleaned output
│   └── run_chunking.py      entry point — runs chunking, writes data/chunks/<court>.jsonl
├── data/
│   ├── raw/                 put/point your PDFs here (gitignored)
│   │   ├── supreme_court/
│   │   └── islamabad_high_court/
│   ├── processed/            one JSON per PDF, accumulates fields through each stage (gitignored)
│   └── chunks/                final output: one .jsonl per court, ready for Module 3 (gitignored)
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

## Run — extraction

```bash
cd ingestion/src
python run_ingestion.py       # Windows: py run_ingestion.py
```

## Run — cleaning

Once extraction has produced output in `data/processed/`, run:

```bash
cd ingestion/src
python run_cleaning.py        # Windows: py run_cleaning.py
```

This reads the already-extracted JSON files and adds `cleaned_text`,
`cleaned_char_count`, and `cleaning_status` to each one — no need to
re-run the (slower) PDF extraction step to test a cleaning change.

### What cleaning fixes

Found by inspecting real extracted text, not guessed at:

1. **Running page headers/footers** (e.g. `C.A. No. 3-L/2016 2`) get
   extracted in the middle of sentences, since pdfplumber has no
   concept of "this is a footer." Detected generically: lines that
   share the same template (ignoring the trailing page number) and
   repeat 2+ times across the document.
2. **Footnote reference numbers glued onto words** (e.g. `Nabi.1`).
   The footnote *text* itself is left alone — those are real
   citations — only the glued-on digit is stripped, and only when it
   looks like a sentence boundary, not a real number (`Appeal No.39`
   is correctly left untouched).
3. Curly quotes/dashes normalized to plain ASCII equivalents, and
   excess whitespace collapsed.

Every rule was tested against the real sample judgments with
explicit pass/fail checks (including two cases that would have been
false positives with a naive implementation) before being applied to
the full batch.

## Run — metadata extraction

```bash
cd ingestion/src
python run_metadata.py        # Windows: py run_metadata.py
```

Extracts case title, court, case number, year, judges, jurisdiction,
hearing/decision dates, and document type (`JUDGMENT` vs
`ORDER_SHEET`) — using a **separate extractor per court**, since SC
and IHC judgments use genuinely different templates. Every field is
optional: a missing field is recorded as `None` and logged as a
warning, never a crash. `citation` is included in the data model but
usually stays empty — court reporters assign citations after
publication, so it's rarely present in the judgment text itself.

## Run — chunking

```bash
cd ingestion/src
python run_chunking.py        # Windows: py run_chunking.py
```

Splits each document's cleaned text into chunks (~1500 characters),
preferring numbered legal paragraphs (`"2. The basic facts..."`) as
the split point where present — that's how judgments are actually
written, and it's a more meaningful retrieval unit than an arbitrary
character window. Falls back to blank-line-separated blocks for
documents without that structure (like short order sheets), and
falls back further to sentence-splitting for any single unit that's
still too large.

**Every chunk carries its parent document's key metadata directly**
(court, case title, case number, year, judges, document type) —
not just an ID to look up later. That's what lets a future RAG
answer cite "which case, which court, which year" straight from the
retrieved chunk, satisfying the project's citation-grounding
requirement (Module 5).

Output: `data/chunks/<court>.jsonl` — one JSON object per line, one
file per court. JSONL rather than one big JSON file so later stages
(embedding generation, Module 3) can stream through chunks without
loading an entire court's output into memory at once.

Two real bugs were caught and fixed by testing chunking against the
actual SC sample before trusting it: a naive sentence-splitting
fallback broke `"Mr. Justice..."` into `"Mr."` and `"Justice..."` as
separate fragments (both are periods followed by a capital letter,
which looks like a sentence boundary to a naive regex), and the same
issue affected numbered-paragraph markers themselves (`"4."` split
off from the sentence it introduces). Both are fixed with explicit
handling, not just avoided in the test case.

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
