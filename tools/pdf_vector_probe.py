#!/usr/bin/env python3
"""Decide, in seconds, whether a PDF's figures can be RIPPED as vector geometry
or whether they are pixels and you are back to computer vision.

WHY THIS EXISTS
---------------
A PDF page is not a picture. It is a display list of drawing commands:

    334.4 554.0 Td (RING MOD) Tj      <- a text object, with its position
    120.5 480.0 m 180.2 480.0 l S     <- a line, with its endpoints
    ... re                            <- rectangles
    ... c                             <- Bezier curves

When a manual's figures are drawn that way, the legends are ALREADY strings and
the lines are ALREADY line segments with coordinates. Extracting them is parsing,
not recognition -- no OCR, no edge detection, no template matching, no error bars.
The command vocabulary maps almost one-to-one onto SVG.

When the figure is instead an embedded raster image, none of that is true and you
need actual computer vision, with everything that implies.

This script tells you which world you are in BEFORE you invest in a pipeline.

WHAT IT REPORTS, PER PAGE
-------------------------
  images      embedded raster XObjects. A figure page with images>0 is suspect;
              a page that is ONE big image is a scan.
  fonts       font resources. Zero fonts on a page with visible text means the
              text was outlined (or it is a scan) -- strings are unrecoverable.
  text runs   extractable text objects.
  m/l/c/re    path operator counts: moveto / lineto / curveto / rectangle.
              High counts mean real line art.

VERDICT
  VECTOR   no raster, real paths, real text        -> rippable, go
  MIXED    paths AND raster on the same page       -> look at it; often a vector
                                                      figure over a raster photo
  RASTER   raster present, few or no paths         -> computer vision territory
  EMPTY    nothing much on the page

CAVEATS, HONESTLY
-----------------
- Operator counts are lexical: this counts occurrences in the decoded content
  stream, and a token like `l` can also appear inside a binary inline image or an
  embedded font program. Treat the numbers as strong signal, not as proof.
- Text can be present but garbled if the font uses a subset encoding with no
  usable ToUnicode map. ALWAYS eyeball the sample strings this prints. A good
  test is to look for a string that exists only in the artwork and nowhere in the
  prose -- on the Nord Lead 2 manual that was `DWN`, a panel legend that is not
  an English word. If it comes out clean, the encoding is sane.
- A vector PDF can still embed individual figures as raster. Check the pages you
  actually care about, not just page 1.

USAGE
    uv run --no-project --with pypdf python pdf_vector_probe.py FILE.pdf
    uv run --no-project --with pypdf python pdf_vector_probe.py FILE.pdf --pages 37-56
    uv run --no-project --with pypdf python pdf_vector_probe.py FILE.pdf --find DWN RING\\ MOD

No quiet fallbacks: a page that cannot be parsed is reported as a loud error line,
never skipped silently.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    sys.exit(
        "pypdf is not installed.\n"
        "Run: uv run --no-project --with pypdf python pdf_vector_probe.py ..."
    )

# Path-construction operators, matched as standalone tokens so that `l` in a word
# is not counted. PDF operators are whitespace-delimited postfix tokens.
PATH_OPERATOR_PATTERNS = {
    "m": re.compile(rb"(?<![A-Za-z0-9])m(?![A-Za-z0-9])"),
    "l": re.compile(rb"(?<![A-Za-z0-9])l(?![A-Za-z0-9])"),
    "c": re.compile(rb"(?<![A-Za-z0-9])c(?![A-Za-z0-9])"),
    "re": re.compile(rb"(?<![A-Za-z0-9])re(?![A-Za-z0-9])"),
}
IMAGE_XOBJECT_PATTERN = re.compile(rb"(?<![A-Za-z0-9])Do(?![A-Za-z0-9])")

VECTOR_PATH_COUNT_THRESHOLD = 40  # below this a page is not carrying real line art


def parse_page_selection(selection_text: str, total_page_count: int) -> list[int]:
    """'37-56' or '9' or '9,37-40' -> zero-based page indices. 1-based input."""
    selected_indices: list[int] = []
    for chunk in selection_text.split(","):
        chunk = chunk.strip()
        if "-" in chunk:
            first_text, last_text = chunk.split("-", 1)
            first, last = int(first_text), int(last_text)
        else:
            first = last = int(chunk)
        if first < 1 or last > total_page_count or first > last:
            sys.exit(
                f"page selection {chunk!r} is outside 1-{total_page_count} "
                f"or reversed -- refusing to guess what you meant"
            )
        selected_indices.extend(range(first - 1, last))
    return selected_indices


def classify_page(image_count: int, path_operator_total: int, text_run_count: int) -> str:
    has_meaningful_paths = path_operator_total >= VECTOR_PATH_COUNT_THRESHOLD
    if image_count == 0 and not has_meaningful_paths and text_run_count == 0:
        return "EMPTY"
    if image_count == 0:
        return "VECTOR" if has_meaningful_paths else "TEXT-ONLY"
    return "MIXED" if has_meaningful_paths else "RASTER"


def probe_pdf(pdf_path: Path, page_indices: list[int] | None, search_strings: list[str]):
    reader = PdfReader(str(pdf_path))
    total_page_count = len(reader.pages)
    indices = page_indices if page_indices is not None else range(total_page_count)

    print(f"\n{pdf_path.name}  ({total_page_count} pages)")
    print(f"{'page':>6} {'images':>7} {'fonts':>6} {'text':>6} "
          f"{'m':>6} {'l':>6} {'c':>6} {'re':>5}  verdict")
    print("-" * 72)

    verdict_tally: dict[str, int] = {}
    string_hits: dict[str, list[int]] = {s: [] for s in search_strings}

    for page_index in indices:
        page = reader.pages[page_index]
        try:
            content_stream_bytes = page.get_contents().get_data()
        except Exception as parse_error:  # loud, never skipped
            print(f"{page_index + 1:>6}  !! CONTENT STREAM UNREADABLE: {parse_error}")
            verdict_tally["ERROR"] = verdict_tally.get("ERROR", 0) + 1
            continue

        operator_counts = {
            name: len(pattern.findall(content_stream_bytes))
            for name, pattern in PATH_OPERATOR_PATTERNS.items()
        }
        path_operator_total = sum(operator_counts.values())

        # Prefer the real XObject resource dict; fall back to counting `Do`.
        resources = page.get("/Resources") or {}
        xobject_dict = resources.get("/XObject") or {}
        try:
            image_count = sum(
                1 for key in xobject_dict
                if (xobject_dict[key].get_object().get("/Subtype") == "/Image")
            )
        except Exception as xobject_error:
            print(f"{page_index + 1:>6}  !! XOBJECT DICT UNREADABLE: {xobject_error}")
            image_count = len(IMAGE_XOBJECT_PATTERN.findall(content_stream_bytes))

        font_count = len(resources.get("/Font") or {})

        extracted_text_runs: list[str] = []

        def collect_text_run(text, _cm, _tm, _font, _size):
            stripped = text.strip()
            if stripped:
                extracted_text_runs.append(stripped)

        page_text = page.extract_text(visitor_text=collect_text_run) or ""

        for needle in search_strings:
            if needle.upper() in page_text.upper():
                string_hits[needle].append(page_index + 1)

        verdict = classify_page(image_count, path_operator_total, len(extracted_text_runs))
        verdict_tally[verdict] = verdict_tally.get(verdict, 0) + 1

        print(f"{page_index + 1:>6} {image_count:>7} {font_count:>6} "
              f"{len(extracted_text_runs):>6} {operator_counts['m']:>6} "
              f"{operator_counts['l']:>6} {operator_counts['c']:>6} "
              f"{operator_counts['re']:>5}  {verdict}")

    print("-" * 72)
    print("verdicts: " + ", ".join(f"{v}={n}" for v, n in sorted(verdict_tally.items())))

    if search_strings:
        print("\nartwork-string probe (a string that exists ONLY as silkscreen is the")
        print("best evidence that figure labels are real text, not outlines):")
        for needle, pages_found in string_hits.items():
            where = ", ".join(str(p) for p in pages_found[:10]) or "NOT FOUND"
            print(f"  {needle!r:20s} {len(pages_found):>3} pages: {where}")

    if verdict_tally.get("VECTOR"):
        print("\n=> VECTOR pages present. The figures are geometry: paths have real")
        print("   coordinates and legends are real strings. Rip them; do not OCR them.")
    elif verdict_tally.get("RASTER") or verdict_tally.get("MIXED"):
        print("\n=> No clean VECTOR pages. Figures are pixels -- computer vision, with")
        print("   the error bars and registration work that implies.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Is this PDF's artwork vector geometry or pixels?"
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--pages", help="1-based, e.g. '9' or '37-56' or '9,37-40'")
    parser.add_argument("--find", nargs="*", default=[],
                        help="strings to hunt for; use one that appears ONLY in artwork")
    args = parser.parse_args()

    if not args.pdf.is_file():
        sys.exit(f"no such file: {args.pdf}")

    reader_for_count = PdfReader(str(args.pdf))
    page_indices = (
        parse_page_selection(args.pages, len(reader_for_count.pages))
        if args.pages else None
    )
    probe_pdf(args.pdf, page_indices, args.find)


if __name__ == "__main__":
    main()
