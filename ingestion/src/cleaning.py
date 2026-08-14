"""
Text cleaning and normalization (Module 2, Session 2.3).

Takes the raw text pulled out by extraction.py and fixes artifacts
introduced by PDF-to-text conversion, before this text is used for
metadata extraction, chunking, or search.

Two real artifacts were found by inspecting actual sample judgments
(not guessed at), and are handled here specifically:

1. Running page headers/footers (e.g. "C.A. No. 3-L/2016 2") get
   extracted right in the middle of sentences, because pdfplumber has
   no concept of "this is a footer" — it just reads what's on the
   page. Each occurrence has a different trailing page number, so
   they aren't literal duplicate lines. They're detected by
   normalizing away the trailing number and looking for a template
   that repeats 2+ times across the document.

2. Footnote reference numbers get glued directly onto words with no
   space (e.g. "Nabi.1"), because that's how they're laid out on the
   page. The footnote TEXT itself is left untouched — those are real
   case citations and are useful, not noise — only the glued-on
   reference digit is stripped.

Both heuristics were tested against real extracted text and
deliberately narrowed to avoid two false positives found during that
testing: a naive version of rule 1 would have deleted the three
"JUDGE" signature lines (real content — shows a 3-judge bench), and
a naive version of rule 2 would have deleted "39" from
"Appeal No.39 of 2014" (a real appeal number, not a footnote).
"""

import re


def remove_repeated_lines(text: str) -> str:
    lines = text.split("\n")

    def normalize(line: str) -> str:
        line = line.strip()
        # Replace a trailing page/line number with a placeholder so
        # "C.A. No. 3-L/2016 2" and "...2016 3" (different pages,
        # same footer template) are recognized as the same pattern.
        return re.sub(r"\d+$", "#", line)

    templates = [normalize(ln) for ln in lines]

    counts: dict[str, int] = {}
    for t in templates:
        if t:
            counts[t] = counts.get(t, 0) + 1

    # Only strip templates that (a) repeat 2+ times AND (b) actually
    # had a trailing number stripped (contain "#") — real running
    # page headers/footers always end in a page number. This avoids
    # stripping genuinely repeated short content with no numbers,
    # like "JUDGE" signature lines, which carry real meaning.
    boilerplate_templates = {
        t for t, count in counts.items() if count >= 2 and "#" in t
    }

    kept = [ln for ln, t in zip(lines, templates) if t not in boilerplate_templates]
    return "\n".join(kept)


def fix_footnote_markers(text: str) -> str:
    # Strips a footnote reference number glued directly onto the end
    # of a sentence (e.g. "Nabi.1" -> "Nabi.", "requirement.2 We" ->
    # "requirement. We"). Only matches when what follows the digit is
    # the start of a new sentence/paragraph (whitespace then an
    # uppercase letter or another digit, or end of string) — NOT when
    # it's followed by a lowercase word, which is what a real inline
    # number looks like (e.g. "Appeal No.39 of 2014" is followed by
    # lowercase "of", so it's correctly left untouched).
    return re.sub(r"\.(\d{1,2})(?=\s+[A-Z0-9]|\s*$)", ".", text)


def normalize_punctuation(text: str) -> str:
    replacements = {
        "\u2018": "'", "\u2019": "'",  # curly single quotes
        "\u201c": '"', "\u201d": '"',  # curly double quotes
        "\u2013": "-", "\u2014": "-",  # en dash, em dash
        "\u00a0": " ",                  # non-breaking space
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def normalize_whitespace(text: str) -> str:
    lines = [ln.rstrip() for ln in text.split("\n")]
    text = "\n".join(lines)
    text = re.sub(r"[ \t]{2,}", " ", text)   # collapse repeated spaces/tabs
    text = re.sub(r"\n{3,}", "\n\n", text)   # collapse 3+ blank lines to 1
    return text.strip()


def clean_text(raw_text: str) -> str:
    text = raw_text
    text = remove_repeated_lines(text)
    text = fix_footnote_markers(text)
    text = normalize_punctuation(text)
    text = normalize_whitespace(text)
    return text
