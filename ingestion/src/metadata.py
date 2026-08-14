"""
Metadata extraction (Module 2, Session 2.4).

Supreme Court and Islamabad High Court judgments use genuinely
different templates (confirmed from real samples), so this uses one
extractor per court rather than a single universal regex — matches
the project's modularity goal: a new court (e.g. Balochistan HC)
gets added later as a new extractor function, without touching the
existing ones.

Philosophy: every field is optional. A missing field is recorded as
None and logged, never a crash — some fields (like `citation`)
usually don't exist in the judgment text at all, since reporters
assign citations after publication.
"""

import re
from typing import Optional

from models import RawDocument


# ---------------------------------------------------------------------
# Shared helpers (used by more than one court's extractor)
# ---------------------------------------------------------------------

def extract_parties(text: str) -> tuple[Optional[str], Optional[str]]:
    """
    Finds a standalone "Versus" line and takes the line immediately
    before it as party 1, and immediately after as party 2. Works for
    both courts' templates. SC-style suffixes like "...Appellant(s)"
    are stripped off since they're a role label, not part of the name.
    """
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.strip().lower() == "versus":
            party1 = lines[i - 1].strip() if i > 0 else None
            party2 = lines[i + 1].strip() if i + 1 < len(lines) else None
            if party1:
                party1 = re.sub(
                    r"\s*\.{2,3}\s*(Appellant|Petitioner)\(s\)\s*$",
                    "", party1, flags=re.IGNORECASE,
                ).strip()
            if party2:
                party2 = re.sub(
                    r"\s*\.{2,3}\s*Respondent\(s\)\s*$",
                    "", party2, flags=re.IGNORECASE,
                ).strip()
            return party1 or None, party2 or None
    return None, None


def detect_document_type(text: str) -> str:
    head = text[:200].upper()
    if "ORDER SHEET" in head:
        return "ORDER_SHEET"
    if "JUDGMENT" in head or "\nJUDGMENT\n" in text.upper():
        return "JUDGMENT"
    return "UNKNOWN"


# ---------------------------------------------------------------------
# Supreme Court extractor
# ---------------------------------------------------------------------

def extract_sc_metadata(text: str) -> dict:
    metadata = {
        "court_name": "Supreme Court of Pakistan",
        "judges": None,
        "case_number": None,
        "year": None,
        "jurisdiction": None,
        "hearing_date": None,
        "decision_date": None,
        "case_title": None,
        "document_type": detect_document_type(text),
    }

    jurisdiction_match = re.search(r"\((\w[\w\s]*Jurisdiction)\)", text)
    if jurisdiction_match:
        metadata["jurisdiction"] = jurisdiction_match.group(1).strip()

    judges = re.findall(r"^(?:Mr\.|Mrs\.|Ms\.)?\s*Justice\s+.+$", text, re.MULTILINE)
    if judges:
        metadata["judges"] = [j.strip() for j in judges]

    case_number_match = re.search(
        r"^([A-Z][A-Z .]*NO\.?\s*[\w\-/]+\s+OF\s+(\d{4}))\s*$", text, re.MULTILINE
    )
    if case_number_match:
        metadata["case_number"] = case_number_match.group(1).strip()
        metadata["year"] = int(case_number_match.group(2))

    hearing_match = re.search(r"Date of Hearing\s*:\s*(\d{2}\.\d{2}\.\d{4})", text)
    if hearing_match:
        metadata["hearing_date"] = hearing_match.group(1)

    # Decision date is typically the last dd.mm.yyyy-style date near
    # the end of the document (after the JUDGE signature block).
    tail = text[-400:]
    date_matches = re.findall(r"\d{2}\.\d{2}\.\d{4}", tail)
    if date_matches:
        metadata["decision_date"] = date_matches[-1]

    appellant, respondent = extract_parties(text)
    if appellant and respondent:
        metadata["case_title"] = f"{appellant} vs {respondent}"

    return metadata


# ---------------------------------------------------------------------
# Islamabad High Court extractor
# ---------------------------------------------------------------------

def extract_ihc_metadata(text: str) -> dict:
    metadata = {
        "court_name": "Islamabad High Court",
        "judges": None,
        "case_number": None,
        "year": None,
        "jurisdiction": None,
        "hearing_date": None,
        "decision_date": None,
        "case_title": None,
        "document_type": detect_document_type(text),
    }

    jurisdiction_match = re.search(r"\((JUDICIAL DEPARTMENT|[\w\s]+DEPARTMENT)\)", text)
    if jurisdiction_match:
        metadata["jurisdiction"] = jurisdiction_match.group(1).strip()

    case_number_match = re.search(
        r"([A-Z][a-zA-Z]*\s+Case\s+No\.?\s*[\w\-/]+\s+of\s+(\d{4}))", text
    )
    if case_number_match:
        metadata["case_number"] = case_number_match.group(1).strip()
        metadata["year"] = int(case_number_match.group(2))

    # The judge's name appears in parentheses directly above the
    # "JUDGE" signature line, e.g. "(MUHAMMAD AZAM KHAN)\nJUDGE".
    judge_match = re.search(r"\(([A-Z][A-Z .]+)\)\s*\n\s*JUDGE", text)
    if judge_match:
        metadata["judges"] = [judge_match.group(1).strip()]

    # Order date: the first dd.mm.yyyy date after an order number
    # like "(03)" at the start of a table row.
    order_date_match = re.search(r"\(\d+\)\s+(\d{2}\.\d{2}\.\d{4})", text)
    if order_date_match:
        metadata["decision_date"] = order_date_match.group(1)

    appellant, respondent = extract_parties(text)
    if appellant and respondent:
        metadata["case_title"] = f"{appellant} vs {respondent}"

    return metadata


# ---------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------

EXTRACTORS = {
    "supreme_court": extract_sc_metadata,
    "islamabad_high_court": extract_ihc_metadata,
}


def extract_metadata(doc: RawDocument, logger) -> RawDocument:
    extractor = EXTRACTORS.get(doc.court)
    text = doc.cleaned_text or doc.raw_text

    if extractor is None or not text:
        doc.metadata_status = "skipped"
        return doc

    try:
        fields = extractor(text)
        for key, value in fields.items():
            setattr(doc, key, value)

        missing = [k for k, v in fields.items() if v is None]
        if missing:
            doc.metadata_status = "partial"
            logger.warning(
                f"[{doc.court}] {doc.filename}: missing fields {missing}"
            )
        else:
            doc.metadata_status = "ok"

    except Exception as e:
        doc.metadata_status = "skipped"
        logger.error(f"[{doc.court}] {doc.filename}: metadata extraction failed — {e}")

    return doc
