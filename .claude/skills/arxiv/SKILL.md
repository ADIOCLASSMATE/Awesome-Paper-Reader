---
name: arxiv
description: Search arXiv and download LaTeX source for academic papers. Use when user says "search arxiv", "download paper", "fetch arxiv", "arxiv search", "get paper source", or wants to find and read papers from arXiv. PDF download is BANNED — only LaTeX source (.tar.gz) is allowed.
argument-hint: [query-or-arxiv-id]
allowed-tools: Bash(*), Read, Grep, Glob, Write
---

# arXiv Paper Search & LaTeX Source Download

Search topic or arXiv paper ID: $ARGUMENTS

> **CRITICAL RULE: PDF is BANNED.** Never download, fetch, or link to PDF files.
> Only download LaTeX source archives from `https://arxiv.org/e-print/ID`.
> LaTeX source can be searched with Grep, read section-by-section with Read,
> and analyzed far more effectively than PDF.

## Constants

- **PAPER_DIR** - Local directory to save downloaded LaTeX source. Default: `papers/inbox/` in the current project directory (dual-zone: inbox for new papers, archive for synthesized papers).
- **MAX_RESULTS = 10** - Default number of search results.
- **FETCH_SCRIPT** - `tools/arxiv_fetch.py` relative to the project root. Fall back to inline Python if not found.

> Overrides (append to arguments):
> - `/arxiv "attention mechanism" - max: 20` - return up to 20 results
> - `/arxiv "2301.07041" - download` - download LaTeX source for a specific paper by ID
> - `/arxiv "query" - dir: literature/` - save source to a custom directory
> - `/arxiv "query" - download: all` - download source for all results

## Workflow

### Step 1: Parse Arguments

Parse `$ARGUMENTS` for directives:

- **Query or ID**: main search term or a bare arXiv ID such as `2301.07041` or `cs/0601001`
- **`- max: N`**: override MAX_RESULTS (e.g., `- max: 20`)
- **`- dir: PATH`**: override PAPER_DIR (e.g., `- dir: literature/`)
- **`- download`**: download the first result's LaTeX source after listing
- **`- download: all`**: download LaTeX source for all results

If the argument matches an arXiv ID pattern (`YYMM.NNNNN` or `category/NNNNNNN`), skip the search and go directly to Step 3.

### Step 2: Search arXiv

Locate the fetch script:

```bash
SCRIPT=$(find tools/ -name "arxiv_fetch.py" 2>/dev/null | head -1)
```

**If SCRIPT is found**, run:

```bash
python3 "$SCRIPT" search "QUERY" --max MAX_RESULTS
```

**If SCRIPT is not found**, fall back to inline Python:

```bash
python3 - <<'PYEOF'
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

NS = "http://www.w3.org/2005/Atom"
query = urllib.parse.quote("QUERY")
url = (f"http://export.arxiv.org/api/query"
       f"?search_query={query}&start=0&max_results=MAX_RESULTS"
       f"&sortBy=relevance&sortOrder=descending")
with urllib.request.urlopen(url, timeout=30) as r:
    root = ET.fromstring(r.read())
papers = []
for entry in root.findall(f"{{{NS}}}entry"):
    aid = entry.findtext(f"{{{NS}}}id", "").split("/abs/")[-1].split("v")[0]
    title = (entry.findtext(f"{{{NS}}}title", "") or "").strip().replace("\n", " ")
    abstract = (entry.findtext(f"{{{NS}}}summary", "") or "").strip().replace("\n", " ")
    authors = [a.findtext(f"{{{NS}}}name", "") for a in entry.findall(f"{{{NS}}}author")]
    published = entry.findtext(f"{{{NS}}}published", "")[:10]
    cats = [c.get("term", "") for c in entry.findall(f"{{{NS}}}category")]
    papers.append({
        "id": aid,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "published": published,
        "categories": cats,
        "abs_url": f"https://arxiv.org/abs/{aid}",
        "source_url": f"https://arxiv.org/e-print/{aid}",
    })
print(json.dumps(papers, ensure_ascii=False, indent=2))
PYEOF
```

Present results as a table:

```text
| # | arXiv ID   | Title               | Authors        | Date       | Category |
|---|------------|---------------------|----------------|------------|----------|
| 1 | 2301.07041 | Attention Is All... | Vaswani et al. | 2017-06-12 | cs.LG    |
```

### Step 3: Fetch Details for a Specific ID

When a single paper ID is requested (either directly or from Step 2):

```bash
python3 "$SCRIPT" paper "ARXIV_ID"
```

Display: title, all authors, categories, full abstract, published date, abstract URL, source URL.

### Step 4: Download LaTeX Source

When download is requested, for each paper ID to download:

```bash
# Using fetch script:
python3 "$SCRIPT" download ARXIV_ID --dir PAPER_DIR
```

The script will:
1. Download `https://arxiv.org/e-print/ARXIV_ID` (LaTeX source archive)
2. Extract to `PAPER_DIR/ARXIV_ID/`
3. List all `.tex` files found with line counts

After each download:

- Confirm the extracted directory contains `.tex` files
- If no LaTeX source is available (404 — scanned/older paper), report it clearly
- Add a 1-second delay between consecutive downloads to avoid rate limiting
- Report: `Downloaded: papers/inbox/2301.07041/ (N .tex files)`

**Once downloaded, read the paper using Read and Grep on the .tex files:**

```bash
# Find the main .tex file (usually main.tex, ms.tex, or paper.tex)
# Read the full paper
Read: papers/inbox/2301.07041/main.tex

# Search for specific content
Grep: "attention" in papers/inbox/2301.07041/

# Read a specific section
Read: papers/inbox/2301.07041/experiments.tex
```

### Step 5: Summarize

For each paper (downloaded or fetched by API):

```markdown
## [Title]

- **arXiv**: [ID] - [abs_url]
- **Authors**: [full author list]
- **Date**: [published]
- **Categories**: [cs.LG, cs.AI, ...]
- **Abstract**: [full abstract]
- **Key contributions** (extracted from abstract):
  - [contribution 1]
  - [contribution 2]
  - [contribution 3]
- **LaTeX source**: papers/inbox/[ID]/ (if downloaded — read .tex files for full content)
```

If LaTeX source was downloaded, additionally extract from the .tex files:
- Methodology details (from method/approach sections)
- Key equations (search for `\begin{equation}`, `\begin{align}`)
- Experimental setup (from experiments section)
- Results tables (search for `\begin{table}`)

### Step 6: Final Output

Summarize what was done:

- `Found N papers for "query"`
- `Downloaded source: papers/inbox/2301.07041/ (N .tex files)` (for each download)
- Any warnings (rate limit hit, no LaTeX source available, already exists)

Suggest follow-up skills:

```text
/read-paper ARXIV_ID      - deep-read this paper from LaTeX source
/search-knowledge "topic"  - search across all read paper notes
```

## Key Rules

- **PDF IS BANNED.** Never download, link to, or suggest PDF files. Only use LaTeX source from `https://arxiv.org/e-print/ID`.
- Always show the arXiv ID prominently - users need it for citations and reproducibility
- Verify downloaded source: directory must contain at least one `.tex` file
- Rate limit: wait 1 second between consecutive source downloads; retry once after 5 seconds on HTTP 429
- Never overwrite an existing source directory - skip it and report "already exists"
- Handle both arXiv ID formats: new (`2301.07041`) and old (`cs/0601001`)
- PAPER_DIR is created automatically if it does not exist
- If a paper has no LaTeX source (scanned/older papers), report this clearly — this paper cannot be read with `/read-paper`
- If the arXiv API is unreachable, report the error clearly and suggest trying again later
- When LaTeX source is available, always prefer reading .tex files over abstract-only summaries
