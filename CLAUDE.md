# Awesome Paper Reader

## Ground Truth

`RESEARCH.md` in the project root is the ground truth for project state.

If present, `.co-researcher/skills.yaml` is the project-local ground truth for preferred skillpacks and supervision preferences.

- Read it at session start.
- Do not rewrite it during normal orchestration unless the user is explicitly running `customize` or editing project preferences.
- Prefer asking the user over guessing when state is ambiguous.

## Session Recovery

On new session or after context compaction:
1. Read `RESEARCH.md` **Pipeline Status** section first (30-second orient).
2. Resume from **Active TODO** — do not restart from scratch.

## CRITICAL: PDF Policy

**Remote PDFs are banned.** Never download, link to, or suggest PDF files from the internet. All remote paper reading uses LaTeX source only.

**Local PDFs are allowed** via `/read-pdf` (docling extraction). When a user provides a local PDF file path, use the `read-pdf` skill to parse it. LaTeX source from arXiv remains the preferred format — always suggest `/read-paper` when an arXiv ID is detected.

- Download LaTeX source from `https://arxiv.org/e-print/ID` (not `/pdf/ID`)
- Source is extracted to `papers/inbox/{arxiv_id}/*.tex` and read with Read/Grep tools
- If a paper has no LaTeX source (scanned/older), suggest `/read-pdf` for local PDFs or read the abstract/HTML version instead
- Remote PDF download is never allowed — no exceptions

## Tools

Python scripts in `tools/` provide API adapters for the skills:

| Script | Purpose | Status |
|--------|---------|--------|
| `tools/arxiv_fetch.py` | arXiv search + LaTeX source download | Available (stdlib only) |
| `tools/daily_papers.py` | Daily LLM paper fetch & filter | Available (OpenAlex for author data — free, no key needed) |
| `tools/pdf_parse.py` | PDF parsing via docling (local files only) | Available (uv managed, requires docling package) |

## Paper Library

Local LaTeX source uses a **dual-zone** structure:

```
papers/
├── inbox/                # Newly read papers (not yet synthesized)
│   └── {arxiv_id}/       # Flat — no domain classification yet
├── archive/              # Synthesized papers, organized by domain
│   ├── safety_alignment/
│   │   └── {arxiv_id}/
│   ├── training_scaling/
│   ├── reasoning/
│   ├── architecture/
│   ├── efficiency/
│   ├── multimodal/
│   ├── retrieval_rag/
│   ├── evaluation/
│   ├── data_synthesis/
│   └── agent/            # Agent-only papers (not cross-cutting)
```

**Lifecycle**: `/read-paper` downloads to `papers/inbox/{id}/` → `/synthesize` moves to `papers/archive/{domain}/{id}/`
- `/read-pdf` parses local PDFs to `papers/inbox/{slug}/` (contains `paper.md`, `metadata.json` instead of `.tex` files)
- `inbox/` = "these are new, not yet organized into insights"
- `archive/` = "these have been classified and synthesized"
- Read papers with `Read: papers/{inbox|archive/...}/{id}/main.tex`
- Search with `Grep: "pattern" in papers/{inbox|archive/...}/{id}/`

## Knowledge Base

Structured paper notes mirror the dual-zone structure:

```
knowledge/
├── inbox/                    # Notes for newly read papers
│   └── summary_{tag}.md     # Not yet synthesized
├── archive/                  # Notes for synthesized papers
│   └── summary_{tag}.md     # Classified and cross-analyzed
├── syntheses/                # /synthesize outputs
│   └── synthesis_YYYY-MM-DD.md
└── daily/                    # daily-papers summaries
    └── YYYY-MM-DD.md
```

- Each note covers: Problem, Method, Key Equations, Experiments, Key Insights, Connections, Questions
- The `Connections` section in each note is critical for cross-paper synthesis
- `/read-paper` writes to `knowledge/inbox/`
- `/read-pdf` also writes to `knowledge/inbox/` (same template, with `**Source**: PDF (via docling)` header)
- `/synthesize` moves notes from `knowledge/inbox/` to `knowledge/archive/` and archives .tex source to `papers/archive/{domain}/`

## Skills — Paper Reading & Analysis

Skills in `.claude/skills/` are invoked by name:

### Core Pipeline
- `daily-papers` — fetch and filter daily LLM papers from arXiv, auto-excludes CV/audio/video/robotics/etc, tiers by relevance (MUST_READ/INTERESTING/MARGINAL/SKIP), checks author quality and institution
- `read-paper` — deep-read an arXiv paper from LaTeX source: download .tex, locate entrypoint, recursively read all sections, produce structured notes (problem/method/experiments/insights/connections) saved to `knowledge/inbox/summary_{tag}.md`
- `read-pdf` — deep-read a local academic PDF using docling: parse PDF to Markdown, produce structured notes. Use when LaTeX source is unavailable. LaTeX source is still preferred when an arXiv ID exists.
- `synthesize` — cross-paper insight formation: reads all notes in knowledge/, classifies papers by research domain, produces detailed per-domain analysis with trends, gaps, and research opportunities saved to `knowledge/syntheses/`

### Search & Review
- `arxiv` — search arXiv API by keyword, download LaTeX source, present structured summaries
- `search-knowledge` — search across all notes in knowledge/ by topic, method, author, or keyword
- `review` — adversarial critique of papers/drafts with FATAL/MAJOR/MINOR severity ratings

### Skill Management
- `customize` — configures the project's skill stack and supervision preferences, writes `.co-researcher/skills.yaml`
- `skillpack` — external skill integration (Personalize), skillpack registry curation (Registry), and skill creation (Create)

## Invocation Graph

- Core pipeline: `daily-papers` → `read-paper` → `synthesize`
- PDF reading: `read-pdf` → `synthesize` (alternative entry point for local PDFs)
- `read-paper` suggests `read-pdf` as fallback when LaTeX source is unavailable
- `arxiv` provides standalone search/download capability
- `search-knowledge` queries the local knowledge base across all notes, syntheses, and daily lists
- `review` runs in isolated context (subagent)
- `skillpack` / `customize` for meta-configuration

## Templates

Templates in `templates/` are copied to project root on init:

- `RESEARCH.md.template` → `RESEARCH.md` (living doc)
- `LESSON.md.template` → `lessons/YYYYMMDD-slug.md` (per-session)
