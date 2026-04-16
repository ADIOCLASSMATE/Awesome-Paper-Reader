#!/usr/bin/env python3
"""PDF parser: extract structured content from local academic PDFs using docling.

Converts PDF to Markdown with section structure and extracts metadata.
No Docker or external services required — runs entirely locally.
"""

import argparse
import json
import pathlib
import re
import sys

SOURCE_DIR_DEFAULT = "papers/inbox"
MAX_PDF_SIZE = 100 * 1024 * 1024  # 100 MB


def _generate_slug(metadata: dict, pdf_path: pathlib.Path) -> str:
    """Generate a slug from the paper title or filename."""
    title = metadata.get("title", "")
    if title:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        slug = re.sub(r"-+", "-", slug)
        return slug[:60]

    stem = pdf_path.stem.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return slug[:60]


def _extract_metadata(result) -> dict:
    """Extract metadata from docling DocumentConverter result."""
    metadata = {"source_type": "pdf"}

    doc = result.document
    if doc is None:
        return metadata

    # Title from document name
    name = getattr(doc, "name", None)
    if name:
        metadata["title"] = str(name)

    # Try to extract from docling's metadata
    doc_meta = getattr(doc, "metadata", None)
    if doc_meta:
        if hasattr(doc_meta, "title") and doc_meta.title:
            metadata["title"] = doc_meta.title
        if hasattr(doc_meta, "authors") and doc_meta.authors:
            metadata["authors"] = [
                {"full": str(a)} for a in doc_meta.authors
            ]
        if hasattr(doc_meta, "date") and doc_meta.date:
            metadata["date"] = str(doc_meta.date)

    return metadata


def _extract_arxiv_id(text: str) -> str | None:
    """Detect arXiv ID in text (filename, title, etc.)."""
    # New format: YYMM.NNNNN
    m = re.search(r"(?<!\d)(\d{4}\.\d{4,5})(?!\d)", text)
    if m:
        return m.group(1)
    # Old format: category/NNNNNNN
    m = re.search(r"([a-z-]+/\d{7})", text)
    if m:
        return m.group(1)
    return None


def parse(
    pdf_path: str,
    output_dir: str = SOURCE_DIR_DEFAULT,
    ocr: bool = True,
    formula: bool = False,
) -> dict:
    """Parse a single PDF using docling, convert to Markdown, extract metadata."""
    from docling.backend.docling_parse_backend import DoclingParseDocumentBackend
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, FormatOption
    from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

    path = pathlib.Path(pdf_path)

    # Validate file
    if not path.exists():
        print(f"Error: file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    if not path.is_file():
        print(f"Error: not a file: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    # Check magic bytes
    header = path.read_bytes()[:5]
    if header != b"%PDF-":
        print(f"Warning: file may not be a valid PDF (magic bytes: {header!r})")

    # Check size
    size = path.stat().st_size
    if size > MAX_PDF_SIZE:
        print(f"Warning: file is large ({size // (1024*1024)} MB), parsing may be slow")

    # Configure pipeline options
    pipeline_options = PdfPipelineOptions(
        do_ocr=ocr,
        do_table_structure=True,
        do_formula_enrichment=formula,
        document_timeout=180.0,
    )

    # Parse with docling
    print(f"Parsing {path.name} ({size // 1024} KB) with docling...")
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: FormatOption(
                pipeline_options=pipeline_options,
                backend=DoclingParseDocumentBackend,
                pipeline_cls=StandardPdfPipeline,
            ),
        }
    )
    result = converter.convert(str(path))

    # Export to Markdown
    markdown = result.document.export_to_markdown()

    # Post-process: remove page number artifacts (bare numbers on their own lines)
    lines = markdown.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Skip lines that are just a number (page number artifact)
        if re.match(r"^\d{1,4}$", stripped):
            continue
        cleaned.append(line)
    markdown = "\n".join(cleaned)

    # Collapse multiple blank lines into at most two
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)

    # Extract metadata
    metadata = _extract_metadata(result)

    # Try to extract title from first heading in Markdown if not in metadata
    if not metadata.get("title") or metadata.get("title", "").startswith(path.stem[:10]):
        lines = markdown.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## ") and not stripped.lower().startswith("## abstract"):
                # First real section heading is often the title
                candidate = stripped[3:].strip()
                if len(candidate) > 10 and len(candidate) < 200:
                    metadata["title"] = candidate
                    break
        # Fallback: use first ## heading of any kind
        if not metadata.get("title") or metadata.get("title", "").startswith(path.stem[:10]):
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("#"):
                    candidate = stripped.lstrip("#").strip()
                    if len(candidate) > 5:
                        metadata["title"] = candidate
                        break

    # Detect arXiv ID
    arxiv_id = _extract_arxiv_id(path.name)
    if not arxiv_id and metadata.get("title"):
        arxiv_id = _extract_arxiv_id(metadata["title"])
    if arxiv_id:
        metadata["arxiv_id"] = arxiv_id

    # Generate slug
    slug = _generate_slug(metadata, path)
    out_path = pathlib.Path(output_dir) / slug
    out_path.mkdir(parents=True, exist_ok=True)

    # Save Markdown
    md_path = out_path / "paper.md"
    md_path.write_text(markdown, errors="replace")

    # Save metadata
    meta_path = out_path / "metadata.json"
    meta_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2)
    )

    # Count sections (lines starting with ##)
    section_count = sum(
        1 for line in markdown.split("\n")
        if line.strip().startswith("## ")
    )

    print(f"Parsed: {out_path}/")
    print(f"  Title: {metadata.get('title', 'N/A')}")
    print(f"  Authors: {len(metadata.get('authors', []))}")
    print(f"  Sections: {section_count}")
    print(f"  Files: paper.md, metadata.json")

    return {
        "slug": slug,
        "output_dir": str(out_path),
        "markdown_file": str(md_path),
        "metadata_file": str(meta_path),
        "metadata": metadata,
    }


def main():
    parser = argparse.ArgumentParser(
        description="PDF parser: extract structured content from academic PDFs (docling)"
    )
    sub = parser.add_subparsers(dest="command")

    # parse subcommand
    p = sub.add_parser("parse", help="Parse a single PDF file")
    p.add_argument("pdf_path", help="Path to local PDF file")
    p.add_argument(
        "--dir", default=SOURCE_DIR_DEFAULT, dest="output_dir",
        help="Output directory (default: papers/inbox)",
    )
    p.add_argument(
        "--no-ocr", action="store_true",
        help="Disable OCR (faster but may miss scanned content)",
    )
    p.add_argument(
        "--formula", action="store_true",
        help="Enable formula enrichment (slower, requires extra model download)",
    )

    args = parser.parse_args()

    if args.command == "parse":
        result = parse(
            args.pdf_path,
            args.output_dir,
            ocr=not args.no_ocr,
            formula=args.formula,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
