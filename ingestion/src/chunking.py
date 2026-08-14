"""
Chunking (Module 2, Session 2.5).

Splits cleaned document text into chunks sized for later embedding
(Module 3), preferring the most legally meaningful structure
available:

1. Numbered paragraphs (e.g. "2. The basic facts are...") — this is
   how judgments are actually written, and testing against the real
   SC sample confirmed it's a reliable signal (9 clean matches).
   Everything before the first numbered paragraph (court name,
   judges, case number, parties) becomes one preamble unit.
2. If a document has no numbered paragraphs (like the short IHC
   order sheet), fall back to blank-line-separated blocks.
3. If any single unit from either of those is still bigger than
   max_chars, it gets split further by sentence.

Why not just always split on blank lines ("\\n\\n")? Tested that
first — it turned out cleaning's page-header removal leaves blank
lines mostly at old PAGE boundaries, not real paragraph boundaries,
so almost the entire document ended up oversized and got routed
through sentence-splitting anyway. Numbered paragraphs are the
actual semantic unit here.

The sentence splitter also had a real bug caught during testing: a
naive version split on every period+capital-letter, which broke
"Mr. Justice..." into "Mr." and "Justice..." as two separate
fragments, since "Mr." ends in a period. Fixed with a small
abbreviation list.
"""

import re

DEFAULT_MAX_CHARS = 1500

ABBREVIATIONS = {"mr", "mrs", "ms", "dr", "no", "vs", "co", "rs", "j"}


def split_into_paragraphs(text: str) -> list:
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def split_into_numbered_paragraphs(text: str) -> list:
    pattern = re.compile(r"(?:^|\n)(\d{1,3}\.\s)")
    matches = list(pattern.finditer(text))

    if len(matches) < 2:
        return []  # not enough structure to be worth using

    units = []
    preamble = text[: matches[0].start()].strip()
    if preamble:
        units.append(preamble)

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        units.append(text[start:end].strip())

    return units


def split_into_sentences(text: str) -> list:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    parts = [p.strip() for p in parts if p.strip()]

    merged = []
    i = 0
    while i < len(parts):
        part = parts[i]

        # A bare paragraph-number fragment (e.g. "4." from "4. For a
        # better understanding...") splits off the same way "Mr."
        # does — merge it forward onto the sentence it introduces,
        # rather than leaving it as its own meaningless fragment.
        if re.fullmatch(r"\d{1,3}\.", part) and i + 1 < len(parts):
            part = part + " " + parts[i + 1]
            i += 1

        if merged:
            prev_tail = merged[-1].rstrip(".").split()
            prev_last_word = prev_tail[-1].lower() if prev_tail else ""
            if prev_last_word in ABBREVIATIONS:
                merged[-1] = merged[-1] + " " + part
                i += 1
                continue

        merged.append(part)
        i += 1

    return [p.strip() for p in merged if p.strip()]


def _greedy_group(units: list, max_chars: int, joiner: str = "\n\n") -> list:
    chunks = []
    current = []
    current_len = 0

    for unit in units:
        unit_len = len(unit)
        if current_len + unit_len > max_chars and current:
            chunks.append(joiner.join(current))
            current, current_len = [], 0
        current.append(unit)
        current_len += unit_len + len(joiner)

    if current:
        chunks.append(joiner.join(current))

    return chunks


def chunk_text(text: str, max_chars: int = DEFAULT_MAX_CHARS) -> list:
    units = split_into_numbered_paragraphs(text)
    if not units:
        units = split_into_paragraphs(text)
    if not units:
        return []

    normalized_units = []
    for unit in units:
        if len(unit) > max_chars:
            normalized_units.extend(split_into_sentences(unit))
        else:
            normalized_units.append(unit)

    return _greedy_group(normalized_units, max_chars)
