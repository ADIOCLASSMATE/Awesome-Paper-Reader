# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Awesome Paper Reader is an arXiv paper reading and knowledge synthesis toolkit built on Claude Code. It automates the daily workflow of discovering, reading, and synthesizing LLM research papers.

Core pipeline: `daily-papers` → `read-paper` → `synthesize`

## CRITICAL: PDF Policy

**Remote PDFs are banned.** Never download, link to, or suggest PDF files from the internet. All remote paper reading uses LaTeX source only.

- Download from `https://arxiv.org/e-print/ID` (not `/pdf/ID`)
- Extracted to `papers/inbox/{arxiv_id}/*.tex`
- Local PDFs are allowed via `/read-pdf` (docling extraction) when no LaTeX source exists
- If an arXiv ID is detected, always suggest `/read-paper` instead of `/read-pdf`

## Tools

Python scripts in `tools/` are the API adapters invoked by skills:

| Script | CLI | Purpose | Dependencies |
|--------|-----|---------|--------------|
| `arxiv_fetch.py` | `search <query>`, `download <id>`, `paper <id>` | arXiv search + LaTeX source download | stdlib only |
| `daily_papers.py` | `fetch`, `run` | Daily LLM paper fetch, relevance scoring, author quality via OpenAlex | stdlib only (OpenAlex is free, no key) |
| `pdf_parse.py` | `parse <pdf_path>` | PDF to Markdown via docling, metadata + arXiv ID detection | docling (uv managed) |

All tools are run via `uv run python tools/<script>`.

### Key tool behaviors

- `arxiv_fetch.py download`: Skips if directory exists; path-traversal protection on tar extraction; handles non-gzip single .tex fallback; aborts on files <1024 bytes (likely error pages)
- `daily_papers.py run`: Relevance scoring with INCLUDE/EXCLUDE keyword dicts (per-tier cap=1 prevents keyword stacking); tier assignment: MUST_READ (≥4), INTERESTING (≥2.5), MARGINAL (≥1), SKIP (<1); OpenAlex author lookup with name normalization and conservative 0.5x scaling for approximate matches
- `pdf_parse.py parse`: Magic-byte validation (`%PDF-`); lazy imports docling; page-number line cleanup; title extraction cascade (docling metadata → first ## heading → first # heading); arXiv ID regex detection to suggest `/read-paper`

## Skills

Skills in `.claude/skills/` are invoked as slash commands:

### Core Pipeline

| Skill | Args | What it does |
|-------|------|-------------|
| `/daily-papers` | `[date]`, `--min-score N`, `--check-authors`, `--categories CATS` | Fetch/filter arXiv LLM papers, tier by relevance, enrich with author data, save to `knowledge/daily/` |
| `/read-paper` | `<arxiv-id-or-url>`, `--focus method\|experiments\|insights`, `--tag NAME` | Download LaTeX source, recursively read all sections, produce structured notes to `knowledge/inbox/summary_{tag}.md` |
| `/read-pdf` | `<local-pdf-path>`, `--focus`, `--tag` | Parse local PDF via docling, produce structured notes (same template, with PDF source header) |
| `/synthesize` | `[domain]`, `--full`, `--since DATE`, `--depth quick\|normal\|deep` | **Two-phase pipeline**: Phase 1 reads .tex source → per-domain deep analyses (`domain_*.md`); Phase 2 reads all domain syntheses → cross-domain synthesis (`synthesis_{date}.md`). Always reads original LaTeX, never just summary notes. |

### Search & Review

| Skill | Args | What it does |
|-------|------|-------------|
| `/arxiv` | `<query-or-id>`, `--max N`, `--download`, `--dir PATH` | Search arXiv API, download LaTeX source, present summaries |
| `/search-knowledge` | `<query>`, `--type notes\|syntheses\|daily\|all`, `--tag TAG` | Multi-strategy search across all notes, syntheses, and daily lists |
| `/review` | (runs in isolated subagent) | Adversarial critique with FATAL/MAJOR/MINOR severity, rubric in `.claude/skills/review/RUBRIC.md` |

### Configuration

| Skill | What it does |
|-------|-------------|
| `/customize` | Interactive skill stack configuration, writes `.co-researcher/skills.yaml` |
| `/skillpack` | Three modes: Personalize (integrate external skills), Registry (curate skillpacks), Create (new skill) |

## Dual-Zone Data Architecture

Both `papers/` and `knowledge/` use the same inbox→archive lifecycle:

```
papers/inbox/{id}/        →  papers/archive/{domain}/{id}/
knowledge/inbox/summary_  →  knowledge/archive/{domain}/summary_
```

- **inbox** = newly read, not yet synthesized
- **archive** = classified by domain, cross-analyzed

`/synthesize` moves both the source files and notes from inbox to archive.

### Research domains (10)

Agent, Safety & Alignment, Reasoning, Training & Scaling, Efficiency, Multimodal, Retrieval & RAG, Evaluation & Benchmark, Architecture, Data & Synthesis

### Note template fields

Problem, Method, Key Equations, Experiments, Key Insights, **Connections** (critical for synthesis), Questions

## Ground Truth

- `RESEARCH.md` — project pipeline state (stage, active TODO, last/next action). Read its **Pipeline Status** section first on session recovery.
- `.co-researcher/skills.yaml` — project-local skill preferences. Do not rewrite unless running `/customize`.

## Templates

Templates in `templates/` are copied to project root on init:

- `RESEARCH.md.template` → `RESEARCH.md`
- `LESSON.md.template` → `lessons/YYYYMMDD-slug.md`
- `skills.yaml.template` → `.co-researcher/skills.yaml`

## Skillpack Presets

`skillpacks/presets/` provides 6 configurations for different research styles:

| Preset | Profile |
|--------|---------|
| `core-only` | Minimal — core skills only |
| `balanced` | Core + ARIS subset (default) |
| `academic-rigor` | Core + academic-research-skills, manual supervision |
| `literature-heavy` | Core + ARIS + feynman + academic + openalex |
| `experiment-heavy` | Core + ARIS + nanoresearch |
| `low-dependency` | Core + ARIS research-lit/experiment-plan only |

## Git Policy

`knowledge/`, `papers/`, `RESEARCH.md`, and `lessons/` are gitignored — this repo ships tools only, not user data.
