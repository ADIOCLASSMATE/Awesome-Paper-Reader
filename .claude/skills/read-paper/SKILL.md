---
name: read-paper
description: Deep-read an arXiv paper from its LaTeX source. Downloads .tex source, locates the entrypoint, recursively reads all section files, and produces structured notes saved to knowledge/. Use when user says "read this paper", "read paper", gives an arXiv URL/ID, or wants detailed notes on a specific paper. PDF IS BANNED — only LaTeX source.
argument-hint: [arxiv-url-or-id]
allowed-tools: Bash(*), Read, Grep, Glob, Write
---

# Read Paper — Deep LaTeX Source Reading

Read paper: $ARGUMENTS

> **CRITICAL RULE: PDF IS BANNED.** Never download, link to, or suggest PDF files.
> All reading is done from local .tex source files only.

## Constants

- **PAPER_DIR** — `papers/inbox/` relative to project root. Newly downloaded LaTeX source goes here.
- **KNOWLEDGE_DIR** — `knowledge/inbox/` relative to project root. Structured notes for new papers go here.
- **FETCH_SCRIPT** — `tools/arxiv_fetch.py` relative to project root.

> Overrides (append to arguments):
> - `/read-paper 2301.07041 - focus: method` — emphasize methodology in notes
> - `/read-paper 2301.07041 - focus: experiments` — emphasize experimental results
> - `/read-paper 2301.07041 - focus: insights` — emphasize key insights and connections
> - `/read-paper 2301.07041 - tag: custom_tag` — override the auto-generated note tag
> - `/read-paper 2301.07041 - no-download` — skip download, assume source already exists locally

## Workflow

### Step 1: Parse Arguments

Parse `$ARGUMENTS` for:

- **arXiv ID or URL**: e.g. `2601.07372` or `https://arxiv.org/abs/2601.07372`
- **`- focus: AREA`**: reading emphasis — `method` / `experiments` / `insights` (default: balanced)
- **`- tag: NAME`**: override the auto-generated tag for the note file
- **`- no-download`**: skip download step, assume .tex source is already in `papers/inbox/`

Normalize the ID:
- Strip URL prefix: `https://arxiv.org/abs/2301.07041` → `2301.07041`
- Strip version suffix: `2301.07041v2` → `2301.07041`
- Validate format: should match `YYMM.NNNNN` or `category/NNNNNNN`

### Step 2: Download LaTeX Source

Unless `- no-download` is specified:

```bash
python3 tools/arxiv_fetch.py download ARXIV_ID
```

This downloads from `https://arxiv.org/e-print/ARXIV_ID`, extracts to `papers/inbox/ARXIV_ID/`, and lists all .tex files.

If the download script places files in `papers/ARXIV_ID/` (old behavior), move them to `papers/inbox/ARXIV_ID/` after download.

If the directory already exists with .tex files, the script will skip the download.

If download fails (no LaTeX source available), report it clearly and stop — this paper cannot be read with this skill.

### Step 3: Locate the Entrypoint

Find the main .tex file that contains `\documentclass`:

```bash
grep -rl '\\documentclass' papers/inbox/ARXIV_ID/
```

Common entrypoint names: `main.tex`, `paper.tex`, `ms.tex`, `acl_latex.tex`, `colm2026_conference.tex`, etc.

The entrypoint is the root of the document — it contains `\begin{document}` and pulls in all other files via `\input{}` or `\include{}`.

### Step 4: Map the Document Structure

From the entrypoint, extract the `\input{}` and `\include{}` directives to build the reading order:

```bash
grep -n '\\input\|\\include' papers/inbox/ARXIV_ID/ENTRYPOINT.tex
```

This gives the logical order of sections. Typical structure:

```text
\input{sections/introduction}
\input{sections/preliminary}
\input{sections/method}
\input{sections/experiment}
\input{sections/related}
\input{sections/conclusion}
\input{sections/appendix}
```

Resolve each input path to an actual file:
- `\input{sections/method}` → `sections/method.tex`
- `\input{Sections/1-Introduction}` → `Sections/1-Introduction.tex`
- Some papers include the `.tex` extension explicitly

Build a reading list in document order.

### Step 5: Read the Paper

Read each file in the reading list using the Read tool. For each file:

1. **Metadata (from entrypoint)**: Extract title, authors, abstract, date
2. **Introduction**: Problem statement, motivation, contributions
3. **Background/Preliminary**: Key definitions, notation, prior work needed
4. **Method**: Core approach, architecture, algorithms, key equations
5. **Experiments**: Setup, datasets, baselines, main results
6. **Related Work**: Positioning against existing work
7. **Conclusion**: Summary, limitations, future work
8. **Appendix** (if relevant): Additional details, proofs, extra experiments

**Reading strategy**:

- Read the entrypoint first for metadata and overall structure
- Then read each section file in order
- For equations: search for `\begin{equation}`, `\begin{align}`, `\begin{algorithm}` — note key formulas
- For tables: search for `\begin{table}` — note main results
- For figures: note captions from `\caption{}` — they often contain key findings
- Skip pure formatting/boilerplate content (style definitions, bibliography)

**If the paper is very long** (many sections, appendix hundreds of lines):
- Read the core sections fully (intro, method, experiments, conclusion)
- For appendix: scan headings and read only sections directly relevant to the focus area
- Note which appendix sections were skipped for transparency

### Step 6: Generate Structured Notes

Produce a structured markdown note and save to `knowledge/inbox/summary_{tag}.md`.

**Tag generation**: Use a short descriptive tag derived from the paper's key concept:
- "Attention Is All You Need" → `self_attention`
- "ClawGuard: Runtime Security..." → `agent_security`
- "AggAgent: Agentic Aggregation..." → `agentic_aggregation`
- Keep tags lowercase, underscore-separated, 2-4 words max
- If `- tag: NAME` override was provided, use that
- Check that the file doesn't already exist — never overwrite

**Note template**:

```markdown
# {Title}

- **arXiv**: [{ID}](https://arxiv.org/abs/{ID})
- **Authors**: {first_author} et al. ({total_authors} authors)
- **Date**: {published_date}
- **Tag**: {tag}

## Problem

{What problem does this paper address? What gap in existing work? 2-4 sentences.}

## Method

{Core approach in 4-8 sentences. Include:
- Key idea / insight
- Architecture or algorithm overview
- Notable design decisions}

### Key Equations

{List 1-3 most important equations or algorithms with brief explanation of what each represents. Use LaTeX notation.}

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
*Generated by read-paper skill from LaTeX source*
*Source: papers/{ID}/*
```

**Focus adjustments**:

When `- focus: AREA` is specified:

- **`method`**: Expand Method section significantly, add more equations and algorithmic details, trim Experiments
- **`experiments`**: Expand Experiments with full result tables, ablation studies, analysis; trim Method
- **`insights`**: Expand Key Insights and Connections, add a "Broader Impact" subsection; trim technical details

### Step 7: Report

Present a brief summary to the user:

```text
Read {Title} ({ID})
  Source: papers/inbox/{ID}/ ({N} .tex files)
  Notes:  knowledge/inbox/summary_{tag}.md

  Problem: {one sentence}
  Method:  {one sentence}
  Result:  {one sentence with key number}

  Key insight: {most important takeaway}
```

Suggest follow-up:

```text
/daily-papers              — discover more papers
/read-paper ANOTHER_ID     — read another paper
(Coming: /synthesize)       — cross-paper analysis and insight formation
```

## Key Rules

- **PDF IS BANNED.** Never download, link to, or suggest PDF files.
- Always download LaTeX source first (unless `- no-download`). Reading abstract-only is not acceptable for this skill.
- The note file must be saved to `knowledge/inbox/summary_{tag}.md`, NOT inside `papers/` or `~/.cache/`.
- Never overwrite an existing note file — pick a different tag if needed.
- Read ALL core sections (intro through conclusion). Skipping sections is only allowed for appendix content.
- Extract actual content from .tex — don't just summarize the abstract. The whole point is deep reading.
- For equations: preserve LaTeX notation in notes so they remain readable.
- For tables: extract key numbers, don't just say "see Table 1".
- The "Connections" section is critical for future synthesize skill — always fill it thoughtfully.
- If a .tex file is empty or contains only boilerplate, skip it and note that.
- Handle papers where `\input` paths don't match actual files gracefully — glob for the closest match.
- Chinese comments in .tex source should be noted (some authors leave implementation notes in comments).
