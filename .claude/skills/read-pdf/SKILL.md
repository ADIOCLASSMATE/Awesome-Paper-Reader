---
name: read-pdf
description: Deep-read a local academic PDF using docling for structured extraction. Parses PDF to Markdown, reads the structured content, and produces notes saved to knowledge/. Use when user says "read this PDF", provides a local PDF path, or wants detailed notes on a paper only available as PDF. LaTeX source from arXiv is still preferred when available.
argument-hint: [path-to-pdf]
allowed-tools: Bash(*), Read, Grep, Glob, Write
---

# Read PDF — Deep PDF Reading via docling

Read PDF: $ARGUMENTS

> **Local PDFs are allowed.** This skill reads local PDF files via docling extraction.
> Remote PDF download is still banned — only local file paths accepted.
> If the paper has an arXiv ID, LaTeX source via `/read-paper` provides higher quality.

## Constants

- **PAPER_DIR** — `papers/inbox/` relative to project root. Parsed Markdown goes here.
- **KNOWLEDGE_DIR** — `knowledge/inbox/` relative to project root. Structured notes go here.
- **PDF_SCRIPT** — `tools/pdf_parse.py` relative to project root.

> Overrides (append to arguments):
> - `/read-pdf /path/to/paper.pdf - focus: method` — emphasize methodology in notes
> - `/read-pdf /path/to/paper.pdf - focus: experiments` — emphasize experimental results
> - `/read-pdf /path/to/paper.pdf - focus: insights` — emphasize key insights and connections
> - `/read-pdf /path/to/paper.pdf - tag: custom_tag` — override the auto-generated note tag

## Workflow

### Step 1: Parse Arguments

Parse `$ARGUMENTS` for:

- **PDF path**: local file path ending in `.pdf` (must exist on disk)
- **`- focus: AREA`**: reading emphasis — `method` / `experiments` / `insights` (default: balanced)
- **`- tag: NAME`**: override the auto-generated tag for the note file

Validate: path exists, file has `.pdf` extension.

### Step 2: Detect arXiv ID

Before parsing, check the PDF filename for arXiv ID patterns (`YYMM.NNNNN` or `category/NNNNNNN`).

If an arXiv ID is found, inform the user:

> "This paper appears to be from arXiv (ID: {id}). LaTeX source provides higher quality reading. Use `/read-paper {id}` instead, or confirm to proceed with PDF."

Wait for user confirmation before proceeding. If no arXiv ID is detected in the filename, proceed directly.

After metadata extraction (Step 3), also check the extracted metadata for an `arxiv_id` field. If found and not previously detected, note it in the report but do not interrupt.

### Step 3: Parse the PDF

Parse the PDF using docling:

```bash
uv run python tools/pdf_parse.py parse "PATH/TO/paper.pdf" --dir papers/inbox
```

This outputs JSON to stdout with:

```json
{
  "slug": "attention-is-all-you-need",
  "output_dir": "papers/inbox/attention-is-all-you-need",
  "markdown_file": "papers/inbox/attention-is-all-you-need/paper.md",
  "metadata_file": "papers/inbox/attention-is-all-you-need/metadata.json",
  "metadata": {
    "title": "...",
    "authors": [{"full": "..."}],
    "date": "...",
    "arxiv_id": "...",
    "source_type": "pdf"
  }
}
```

Parse the JSON to get the Markdown file path and metadata.

If parsing fails (docling error, malformed PDF), report the error clearly and suggest:
- Trying a different PDF version
- Using the paper's arXiv ID with `/read-paper` if available

### Step 4: Read the Paper

Read the generated Markdown file using the Read tool. The Markdown from docling includes:

- Section headings (`## Section Name`) preserving the paper's structure
- Paragraph text with reasonable formatting
- Tables converted to Markdown where possible
- Figure/image placeholders with captions

Reading strategy:

1. Read `metadata.json` first for structured author/date/arXiv ID info
2. Read `paper.md` — for longer papers, read in sections if the file is large
3. For figures: note any image/figure placeholders and their captions
4. For tables: extract key numbers from the Markdown tables

**Quality caveat**: docling's extraction is good but not perfect compared to LaTeX source. Some equations may not render correctly, and figure content is lost (only captions preserved). Note any sections where extraction quality seems poor.

### Step 5: Generate Structured Notes

Produce a structured markdown note and save to `knowledge/inbox/summary_{tag}.md`.

**Tag generation**: Use a short descriptive tag derived from the paper's key concept:
- "Attention Is All You Need" → `self_attention`
- Keep tags lowercase, underscore-separated, 2-4 words max
- If the metadata has an `arxiv_id`, use `summary_{arxiv_id_with_underscores}` for consistency with `/read-paper` (e.g., `summary_2604_12782`)
- If `- tag: NAME` override was provided, use that
- Check that the file doesn't already exist — never overwrite

**Note template**:

```markdown
# {Title}

- **Source**: PDF (via docling)
- **PDF path**: {original_pdf_path}
- **Authors**: {first_author} et al. ({total_authors} authors)
- **Date**: {date}
- **Tag**: {tag}
{arXiv_id_line}

## Problem

{What problem does this paper address? What gap in existing work? 2-4 sentences.}

## Method

{Core approach in 4-8 sentences. Include:
- Key idea / insight
- Architecture or algorithm overview
- Notable design decisions}

### Key Equations

{List 1-3 most important equations or algorithms with brief explanation of what each represents. Use LaTeX notation. If equations were not fully extractable from PDF, note: "Equations not fully extractable from PDF — see original paper."}

## Experiments

### Setup

- **Benchmarks/Datasets**: {list}
- **Baselines**: {list}
- **Metrics**: {list}
- **Models tested**: {list}

### Main Results

{Key findings in 2-4 sentences. Reference specific numbers from tables.}

## Key Insights

{2-5 bullet points capturing the most important takeaways:
- What did we learn that wasn't obvious before?
- What design choices matter and why?
- What are the limitations or caveats?}

## Connections

{How does this relate to other work? Identify:
- Builds on: {prior work this extends}
- Related to: {contemporary work on similar problems}
- Enables: {what future work this could support}
- Contrasts with: {work that takes a different approach}}

## Questions for Further Exploration

{2-3 open questions this paper raises or doesn't fully answer}

---
*Generated by read-pdf skill from PDF via docling*
*Source: papers/inbox/{slug}/*
*Note: docling extraction may have missed or garbled some equations/figures*
```

Where `{arXiv_id_line}` is:
- If arXiv ID was found: `- **arXiv**: [{ID}](https://arxiv.org/abs/{ID})`
- If not: omitted

**Focus adjustments** (same as read-paper):

When `- focus: AREA` is specified:
- **`method`**: Expand Method section significantly, add more equations and algorithmic details, trim Experiments
- **`experiments`**: Expand Experiments with full result tables, ablation studies, analysis; trim Method
- **`insights`**: Expand Key Insights and Connections, add a "Broader Impact" subsection; trim technical details

### Step 6: Report

Present a brief summary to the user:

```text
Read {Title} (PDF)
  Source: papers/inbox/{slug}/ (docling extraction)
  Notes:  knowledge/inbox/summary_{tag}.md

  Problem: {one sentence}
  Method:  {one sentence}
  Result:  {one sentence with key number}

  Key insight: {most important takeaway}

  Quality note: {any sections where docling extraction was incomplete}
```

Suggest follow-up:

```text
/read-paper ARXIV_ID     — re-read from LaTeX source (higher quality) if arXiv ID found
/daily-papers            — discover more papers
/synthesize              — cross-paper analysis
```

## Key Rules

- **Remote PDFs are banned.** Only local PDF file paths are accepted. Never download a PDF from the internet.
- **LaTeX source is preferred when available.** If the paper has an arXiv ID, always suggest `/read-paper` as the higher-quality alternative.
- docling extraction quality varies by PDF. Always note which sections had extraction issues (missing equations, garbled text, etc.).
- The note file must be saved to `knowledge/inbox/summary_{tag}.md`, NOT inside `papers/`.
- Never overwrite an existing note file — pick a different tag if needed.
- The "Connections" section is critical for future `/synthesize` — always fill it thoughtfully.
- If docling fails to parse the PDF at all, report the error clearly and suggest alternatives.
- The `papers/inbox/{slug}/` directory contains `paper.md` and `metadata.json` — preserve both for potential re-processing.
- Use `uv run python tools/pdf_parse.py` for all script invocations (not bare `python3`).
