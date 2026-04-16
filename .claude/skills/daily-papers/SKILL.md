---
name: daily-papers
description: Fetch and filter daily LLM papers from arXiv. Only surfaces large language model related work — excludes CV, audio/video generation, robotics, and other non-LLM topics. Scores relevance, checks author quality, and tiers papers as MUST_READ / INTERESTING / MARGINAL / SKIP. Use when user says "daily papers", "today's papers", "what's new on arxiv", "find new LLM papers", or "check new papers".
argument-hint: [date-or-empty-for-today]
allowed-tools: Bash(*), Read, Write, WebFetch
---

# Daily LLM Papers

Fetch, filter, and tier today's LLM papers from arXiv.

> **Scope**: Large language models only. CV, audio/video generation, robotics,
> medical imaging, wireless, recommender systems, and other non-LLM topics are
> automatically excluded.

## Constants

- **CATEGORIES** — arXiv categories to scan: `cs.CL, cs.AI, cs.LG`
- **MAX_FETCH = 150** — Max papers to fetch per run
- **MIN_SCORE = 0.5** — Minimum relevance score to surface
- **FETCH_SCRIPT** — `tools/daily_papers.py` relative to project root

> Overrides (append to arguments):
> - `/daily-papers` — today's papers (default)
> - `/daily-papers 2026-04-10` — papers from a specific date
> - `/daily-papers - min-score: 2` — only high-relevance papers
> - `/daily-papers - check-authors: true` — look up first author on Semantic Scholar (slow)
> - `/daily-papers - categories: cs.CL` — only NLP category
> - `/daily-papers - max: 300` — fetch more papers

## Workflow

### Step 1: Parse Arguments

Parse `$ARGUMENTS` for:

- **Date**: `YYYY-MM-DD` format, or empty for today
- **`- min-score: N`**: override MIN_SCORE (default 0.5; use 2 for strict filtering)
- **`- check-authors: true`**: enable OpenAlex author quality lookup (free, no API key, ~0.3s per paper)
- **`- categories: CATS`**: override CATEGORIES
- **`- max: N`**: override MAX_FETCH

### Step 2: Fetch and Filter

Run the fetch script:

```bash
python3 tools/daily_papers.py run \
  --date "DATE" \
  --categories "CATEGORIES" \
  --max MAX_FETCH \
  --min-score MIN_SCORE \
  --check-authors  # only if requested
```

If `tools/daily_papers.py` is not found, fall back to inline arXiv API search
with manual keyword filtering (less precise but works).

### Step 3: Present Results

Present papers grouped by tier:

#### MUST_READ (score ≥ 4)

```text
| # | arXiv ID | Title | Authors | Score | Author Quality |
|---|----------|-------|---------|-------|---------------|
```

For each MUST_READ paper, also show:
- **Why relevant**: Which LLM keywords triggered the high score
- **First author**: Name + institution (if detected) + S2 profile (if checked)
- **Abstract**: Full abstract for quick assessment

#### INTERESTING (score 2–3.9)

Same table format, but only show first 2 lines of abstract.

#### MARGINAL (score 0.5–1.9)

Compact table only — title and score. No abstract.

### Step 4: Author Quality Assessment

When `check-authors` is enabled (or for MUST_READ papers by default):

1. **First author OpenAlex profile**: h-index, citation count, works count
2. **Institution detection**: Match against known institution lists
   - **Tier 1**: OpenAI, DeepMind, Anthropic, Meta FAIR, Google Research/Brain, MS Research, top US/UK/CN universities
   - **Tier 2**: Strong regional universities, major tech companies (Alibaba, ByteDance, Tencent, Baidu, Huawei)
   - **Unknown**: No match found

3. **Author quality labels**:
   - `high` — h-index ≥ 20 OR citations ≥ 5000 (established researcher)
   - `medium` — h-index ≥ 10 OR citations ≥ 1000 (productive researcher)
   - `low` — citations ≥ 100 but no strong track record (early career or potentially water papers)
   - `unknown` — OpenAlex lookup failed or no profile found

4. **Water paper signals** (flag, don't auto-exclude):
   - First author with very low citation count AND from unknown institution
   - Title contains "survey" or "review" from unknown group
   - Paper is solely about applying existing method to a new domain without innovation
   - Multiple papers from same group with near-identical titles in short timeframe

### Step 5: Save Summary

Save a dated summary to `knowledge/daily/`:

```
knowledge/daily/YYYY-MM-DD.md
```

Format:

```markdown
# Daily LLM Papers — YYYY-MM-DD

## MUST_READ (N)

### [Title](arxiv_url)
- **Authors**: First Author et al. | **Institution**: [detected or Unknown] | **Quality**: [high/medium/low]
- **Score**: X.X | **Why**: [key LLM keywords that matched]
- **Abstract**: [full abstract]

## INTERESTING (N)

| Paper | Score | Authors | Note |
|-------|-------|---------|------|

## SKIPPED (N non-LLM papers filtered out)

Top skipped: [list 3-5 titles that were close to threshold]
```

### Step 6: Suggest Follow-up

For MUST_READ papers:

```text
/arxiv "ARXIV_ID" - download    — download LaTeX source and read in detail
/research-lit "topic"            — broader literature context
```

## Relevance Scoring Logic

The scoring system uses weighted keyword matching:

**Positive signals (LLM relevance)**:
- **+2**: Core LLM keywords — "large language model", "LLM", "RLHF", "DPO", "chain-of-thought", "scaling law", "fine-tuning", specific model names (GPT-4, LLaMA, DeepSeek, etc.)
- **+1**: LLM-adjacent — "transformer", "MoE", "quantization", "RAG", "agent", "multimodal", "safety", "alignment", "KV cache", "language model"
- **+0.5**: Tangential — "NLP", "pretrain", "benchmark", "evaluation"

**Negative signals (non-LLM exclusion)**:
- **-3**: Strong exclude — "object detection", "video synthesis", "speech recognition", "medical imaging", "protein", "autonomous driving", "recommender system", "GAN"
- **-1**: Mild exclude — "diffusion model" (unless paired with LLM keywords), "image generation", "video generation"

**Tier thresholds**:
- `MUST_READ` ≥ 4: Directly about LLM methodology, training, or capabilities
- `INTERESTING` ≥ 2: LLM-related but may be application-focused or peripheral
- `MARGINAL` ≥ 0.5: Tangentially related, probably not core LLM work
- `SKIP` < 0.5: Not LLM-related

## Key Rules

- **PDF IS BANNED.** Never suggest downloading PDFs. Only LaTeX source.
- Only surface LLM papers. If in doubt, exclude rather than include.
- Author quality is advisory, not deterministic — a paper from an unknown author
  can still be MUST_READ if the content is clearly important.
- Water paper flags are signals, not verdicts. Present them and let the user decide.
- Always show WHY a paper was scored the way it was (which keywords matched).
- For MUST_READ papers from top institutions, highlight the institution.
- The scoring system is conservative: better to miss a borderline paper than
  to flood the user with irrelevant work.
- If the arXiv API is unreachable, suggest checking https://huggingface.co/papers
  or https://x.com/akaboratory as fallback.
