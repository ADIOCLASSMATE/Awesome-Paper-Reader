---
name: synthesize
description: Synthesize insights across all read papers. Two-phase pipeline — Phase 1 produces per-domain deep analyses from .tex source, Phase 2 produces cross-domain synthesis from domain analyses. Always reads original LaTeX, never just summary notes. Use when user says "synthesize", "summarize all papers", "what insights", "organize my readings", "research trends", or "give me an overview".
argument-hint: [domain-or-empty-for-all]
allowed-tools: Bash(*), Read, Grep, Glob, Write, Agent
---

# Synthesize — Cross-Paper Insight Formation

Synthesize: $ARGUMENTS

> **CRITICAL RULES:**
> 1. **PDF IS BANNED.** Never download or link to PDF files.
> 2. **NOTES ALONE ARE INSUFFICIENT.** Per-domain analysis MUST read from .tex source files in `papers/archive/{domain}/{id}/` or `papers/inbox/{id}/`. Summary notes are used for classification and cross-referencing only — the actual technical content, equations, experimental details, and nuanced findings must come from the original LaTeX.
> 3. **Shallow synthesis is unacceptable.** Every domain analysis must trace technical threads with evidence, identify contradictions, and expose open gaps with untried combinations.

## Constants

- **KNOWLEDGE_DIR** — `knowledge/` relative to project root. Contains notes in `inbox/` and `archive/`.
- **DAILY_DIR** — `knowledge/daily/` relative to project root. Contains daily paper lists.
- **PAPERS_DIR** — `papers/` relative to project root. Contains LaTeX source in `inbox/` and `archive/`.
- **OUTPUT_DIR** — `knowledge/syntheses/` relative to project root. Synthesis outputs go here.
- **DOMAIN_SYNTHESES** — Per-domain synthesis files: `knowledge/syntheses/domain_{domain}.md`
- **CROSS_DOMAIN_SYNTHESIS** — Final synthesis: `knowledge/syntheses/synthesis_{date}.md`

## Dual-Zone Architecture

Papers and notes follow a lifecycle:

```
/read-paper → papers/inbox/{id}/ + knowledge/inbox/summary_{tag}.md   (new, unorganized)
/synthesize → papers/archive/{domain}/{id}/ + knowledge/archive/{domain}/summary_{tag}.md  (classified, cross-analyzed)
```

- **inbox/** = newly read papers, not yet synthesized into insights
- **archive/** = papers that have been classified by domain and cross-analyzed

When synthesizing:
1. Read notes from BOTH `knowledge/inbox/` AND `knowledge/archive/` (archive provides established context)
2. After synthesis, move inbox papers/notes to archive (classified by domain)
3. Papers already in archive stay in place

> Overrides (append to arguments):
> - `/synthesize` — synthesize across all papers (default)
> - `/synthesize agent` — focus on a specific domain only (skips Phase 2)
> - `/synthesize - full` — force complete re-synthesis, ignore cached domain syntheses
> - `/synthesize - since: 2026-04-01` — only include papers read after this date
> - `/synthesize - depth: deep` — exhaustive analysis with equation-level connections (default for Phase 1)
> - `/synthesize - depth: quick` — brief overview (reads notes only, no .tex)

## Two-Phase Pipeline

The synthesis operates in two phases. This is **mandatory**, not optional:

```
Phase 1: Per-Domain Deep Analysis (from .tex source)
  ├── Read .tex source for every paper in each domain
  ├── Produce domain_{domain}.md for each domain
  └── Can be parallelized across domains via agents

Phase 2: Cross-Domain Synthesis (from domain syntheses)
  ├── Read all domain_*.md files produced in Phase 1
  ├── Identify convergent/divergent threads across domains
  ├── Produce synthesis_{date}.md
  └── Must read ALL domain files before writing
```

**Why two phases?** Per-domain analysis requires deep reading of .tex source (thousands of lines per paper). Cross-domain synthesis requires holistic view across all domains. Combining them in one pass leads to shallow analysis — which is exactly what this skill is designed to prevent.

---

## Phase 1: Per-Domain Deep Analysis

### Step 1: Parse Arguments

Parse `$ARGUMENTS` for:

- **Domain filter**: optional — only synthesize papers in a given research domain (e.g. "agent", "reasoning", "safety")
- **`- full`**: force complete re-synthesis from scratch, delete any previous synthesis files
- **`- since: DATE`**: only include papers whose note date is on or after DATE (YYYY-MM-DD)
- **`- depth: LEVEL`**: `quick` (notes only, fast) / `normal` (selective .tex reading) / `deep` (full .tex reading, default)

**If `depth: quick`**: Skip .tex reading entirely. Use summary notes only. Produce abbreviated domain analyses. This is appropriate only for quick check-ins, not for real synthesis.

### Step 2: Collect and Classify Papers

Scan both inbox and archive for paper notes:

```bash
# Inbox — newly read, not yet synthesized
find knowledge/inbox/ -name "summary_*.md" | sort

# Archive — previously synthesized
find knowledge/archive/ -name "summary_*.md" | sort
```

Read each note fully for classification. For each paper, determine:

- **Primary domain**: the domain where the paper makes its main contribution
- **Secondary domains**: any other domains the paper touches
- **Key contribution type**: `novel_method` / `new_benchmark` / `empirical_study` / `theoretical` / `framework` / `analysis`

**LLM research domains** (non-exhaustive — add new domains as they emerge):

| Domain | Covers |
|--------|--------|
| **Agent** | Tool use, function calling, MCP, agentic frameworks, planning, web navigation |
| **Safety & Alignment** | Jailbreak, red-teaming, prompt injection, RLHF alternatives, safety benchmarks |
| **Reasoning** | Chain-of-thought, test-time compute, search, planning, mathematical reasoning |
| **Training & Scaling** | Pre-training data, scaling laws, fine-tuning methods, RLHF/DPO, distillation |
| **Efficiency** | Quantization, pruning, speculative decoding, KV cache, inference optimization |
| **Multimodal** | Vision-language, audio-language, any cross-modal LLM work |
| **Retrieval & RAG** | Retrieval-augmented generation, long context, knowledge-intensive tasks |
| **Evaluation & Benchmark** | New benchmarks, evaluation methodology, human preference |
| **Architecture** | New model architectures, MoE, attention variants, tokenization |
| **Data & Synthesis** | Synthetic data, data quality, data mixing, data contamination |

Build a classification table:

```text
| Paper | Tag | Primary Domain | Secondary | Type |
|-------|-----|---------------|-----------|------|
```

Also scan `knowledge/daily/` for daily paper lists (provides context on what was available but not read):

```bash
find knowledge/daily/ -name "*.md" | sort
```

**If no notes exist in either inbox or archive**: Report that there are no read papers to synthesize. Suggest running `/daily-papers` and `/read-paper` first.

### Step 3: Per-Domain .tex Reading and Analysis

For **each domain that has papers**, produce a detailed domain synthesis. This step MUST read from .tex source files.

**How to locate .tex source**: For each paper in a domain, the .tex source is at:
- `papers/archive/{domain}/{arxiv_id}/` (archived papers)
- `papers/inbox/{arxiv_id}/` (new papers not yet archived)

**Reading strategy for .tex files**:
- Start with the main .tex file (usually `main.tex`, `acl_latex.tex`, or the largest .tex file)
- Read the full main text (Abstract through Conclusion). Skip `\appendix` and everything after it — large .tex files are almost always large because of appendices (proofs, supplementary experiments, prompts), not main content
- For papers with multiple .tex files (sections split across files), read all substantive section files, but skip files clearly named `appendix*`, `supplement*`, `supp*`, `extra*`
- If a paper's main body .tex is still very large after excluding appendices (>3MB), it likely contains excessive figures/tables inline — read it in chunks, focusing on prose sections

#### Domain Synthesis Output Template

Save to `knowledge/syntheses/domain_{domain_name}.md`:

```markdown
# Domain Synthesis: {Domain Name}

**Date**: {date}
**Papers**: {N}
**Scope**: {one-sentence description of what this domain's papers cover}

---

## 1. Paper Landscape

| # | Paper | One-Line Contribution | Positioning |
|---|-------|----------------------|-------------|
{table with all papers, their core contribution, and how they relate to prior work}

**Overall arc**: {1-2 sentences describing the overarching narrative across these papers}

---

## 2. Technical Thread

### Thread A: {Thread Name}

{Trace the evolution of ideas within this thread. For each paper in the thread:
- What problem did it solve that prior work couldn't?
- What assumption does it make or challenge?
- How does it connect to other papers in the thread?

Be specific — cite equations, experimental results, and methodological details from the .tex source.}

### Thread B: {Thread Name}

{Repeat for each major thread. Typically 2-4 threads per domain.}

### Shared Assumptions

- {Assumption 1}: Which papers hold it? Is it justified?
- {Assumption 2}: ...

### Divergence Points

- Where papers disagree or take fundamentally different approaches to the same problem

---

## 3. Key Findings

### Aggregated Results

| Paper | Key Metric | Main Result |
|-------|-----------|-------------|
{quantitative results table}

### Agreements

1. **{Finding}**: {Which papers confirm it, with specific evidence}
2. ...

### Contradictions and Tensions

1. **{Tension}**: {Paper A claims X, Paper B shows Y. Possible resolution: ...}
2. ...

---

## 4. Open Gaps

### Unsolved Problems

1. **{Problem}**: {Why it matters, what's blocking progress}

### Unchallenged Assumptions

1. **{Assumption}**: {Why it might be wrong, what evidence challenges it}

### Untried Combinations

1. **{Combination}**: {Paper A's method + Paper B's insight. Why it could work. What would need to change.}

---

## 5. Research Trends

### Converging Trends

1. **{Trend}**: {Which papers demonstrate it, what's driving convergence}

### Still Debated

1. **{Question}**: {Positions taken by different papers, what evidence would resolve it}

---

## 6. Methodological Comparison Table

| Approach | Key Assumption | Limitations | Scale | Main Result |
|----------|---------------|-------------|-------|-------------|
{structured comparison of all methods in the domain}
```

**Critical requirements for domain synthesis**:
- Every claim must reference specific evidence from the .tex source (not just the summary note)
- Technical threads must trace idea evolution with specific methodological details
- Contradictions must be analyzed, not just listed
- Untried combinations must explain *why* they could work, not just that they haven't been tried
- The methodological comparison table must be complete for all papers in the domain

#### Parallel Execution

When synthesizing all domains (no domain filter), **use parallel agents** to produce domain syntheses simultaneously:

```
For each domain with papers:
  Spawn Agent (subagent_type="general-purpose") with:
    - List of papers in this domain (arxiv_id, tag, notes path, .tex source path)
    - Domain synthesis template
    - Instructions to read ALL .tex source files and produce the domain analysis
    - Output file path: knowledge/syntheses/domain_{domain}.md
```

**Agent prompt must include**:
1. The exact .tex file paths for each paper in the domain
2. The full domain synthesis template (sections 1-6)
3. Explicit instruction: "YOU MUST WRITE THE OUTPUT FILE before finishing. Read all .tex sources first, then write the complete domain synthesis."
4. For papers with very large .tex files (>3MB after excluding appendices): "Read main text in chunks, focusing on prose sections. Skip inline figures/tables if needed to conserve context."

**If an agent fails** (context exhaustion, API error):
- Retry with reduced scope: mark the largest .tex files as "NOTE ONLY"
- Ensure the retry prompt includes "YOU MUST WRITE THE FILE" instruction
- Maximum 2 retries per domain

### Step 4: Check Phase 1 Completion

Before proceeding to Phase 2, verify:

```bash
ls knowledge/syntheses/domain_*.md
```

All domains with papers must have a corresponding domain synthesis file. If any are missing, produce them now.

**If `- full` is specified**: Delete existing domain synthesis files before Phase 1, forcing complete re-synthesis.

---

## Phase 2: Cross-Domain Synthesis

### Step 5: Read All Domain Syntheses

Read EVERY `domain_*.md` file produced in Phase 1. Do NOT skip any — cross-domain insights emerge from reading across all domains, not cherry-picking.

```bash
find knowledge/syntheses/ -name "domain_*.md" | sort
```

Read each file fully using the Read tool.

### Step 6: Cross-Domain Analysis

After reading all domain syntheses, identify:

**Convergent Threads**: Where different domains converge on the same insight or principle.
- Must cite specific papers from different domains that independently arrive at the same conclusion
- Provide evidence tables showing the convergence
- Explain the mechanism: why do different approaches lead to the same finding?

**Divergent Approaches**: Where similar problems are tackled with fundamentally different approaches across domains.
- Must present both sides with evidence
- Analyze why the divergence exists (different assumptions? different constraints? different evaluation criteria?)
- Identify conditions under which each approach is superior

**Underexplored Intersections**: What domain combinations have potential but lack papers connecting them.
- Must explain *why* the intersection is promising (what does each domain contribute?)
- Must identify specific paper pairs or methods that could be combined
- Assess feasibility (low barrier = existing methods can compose; high barrier = requires new architecture)

**Meta-Observations**: Patterns across the entire reading corpus.
- What methodologies are becoming standard across domains?
- What evaluation practices need improvement?
- What assumptions does the field take for granted that might be wrong?

### Step 7: Research Opportunity Map

Produce a prioritized list of research opportunities:

```text
| Priority | Opportunity | Domain(s) | Evidence | Feasibility |
|----------|------------|-----------|----------|-------------|
| HIGH  | {description} | {domains} | {which papers/gaps} | {assessment} |
| MEDIUM | {description} | {domains} | {which papers/gaps} | {assessment} |
| LOW   | {description} | {domains} | {which papers/gaps} | {assessment} |
```

Criteria for priority:
- **HIGH**: Multiple papers across domains point to the gap, solution seems tractable, high impact potential
- **MEDIUM**: Gap identified but solution unclear, or single domain points to it
- **LOW**: Speculative, requires significant resources, or unclear impact

### Step 8: Archive Inbox Papers

After producing the cross-domain synthesis, **move all inbox papers and notes to the archive**, organized by domain.

For each paper that was in `knowledge/inbox/`:

1. **Determine its domain** from the classification in Step 2
2. **Move the knowledge note** from `knowledge/inbox/summary_{tag}.md` to `knowledge/archive/{domain}/summary_{tag}.md`
   - Create the domain directory if it doesn't exist: `mkdir -p knowledge/archive/{domain}`
3. **Move the .tex source** from `papers/inbox/{id}/` to `papers/archive/{domain}/{id}/`
   - Create the domain directory if it doesn't exist: `mkdir -p papers/archive/{domain}`
   - Domain directory names use snake_case: `safety_alignment`, `training_scaling`, `reasoning`, `architecture`, `efficiency`, `multimodal`, `retrieval_rag`, `evaluation`, `data_synthesis`, `agent`

**Both `knowledge/archive/` and `papers/archive/` must use the same domain subdirectory structure.**

**Papers already in archive are NOT moved** — they stay in their existing domain directory.

After archiving, verify:
- `knowledge/inbox/` should be empty (or contain only notes that were not part of this synthesis)
- `papers/inbox/` should be empty (or contain only papers that were not part of this synthesis)
- `knowledge/archive/` contains all synthesized notes
- `papers/archive/{domain}/` contains all synthesized .tex sources

### Step 9: Save Cross-Domain Synthesis Output

Save to `knowledge/syntheses/synthesis_{date}.md`:

**Output format**:

```markdown
# Research Synthesis — {date}

- **Papers analyzed**: {N} (all read from .tex source)
- **Domains identified**: {N}
- **Date range**: {earliest} to {latest}
- **Depth**: {quick/normal/deep}

## Classification

### New Papers (Inbox → Archive)

| Paper | Tag | Primary Domain | Secondary | Type |
|-------|-----|---------------|-----------|------|
{table}

### Previously Archived Papers ({N})

Classified across all {N} domains; see individual domain syntheses for full listing.

---

## Domain Summaries

| Domain | Papers | Core Finding |
|--------|--------|-------------|
{one-row-per-domain summary table}

---

## Cross-Domain Synthesis

### Convergent Thread 1: {Thread Name}

{Detailed analysis with evidence table across domains}

### Convergent Thread 2: {Thread Name}

{...}

### Divergent Thread 1: {Thread Name}

{Detailed analysis showing opposing approaches}

### Underexplored Intersection 1: {Intersection}

{Why promising, what each domain contributes, feasibility}

{...}

---

## Research Opportunity Map

| Priority | Opportunity | Domain(s) | Evidence | Feasibility |
|----------|------------|-----------|----------|-------------|
{table}

---

## Reading Recommendations

### Fill gaps in existing domains
- {paper suggestion} — would clarify {gap}

### Expand into new domains
- {domain suggestion} — currently underrepresented in readings

### Follow citation trails
- {paper} cited in {read paper} looks important because {reason}

---

*Generated by synthesize skill (two-phase, .tex-level reading)*
*Next: /daily-papers to discover more, /read-paper ID to read specific papers*
```

### Step 10: Report

Present a concise summary to the user:

```text
Synthesized {N} papers across {M} domains
  Phase 1: {M} domain syntheses → knowledge/syntheses/domain_*.md
  Phase 2: Cross-domain synthesis → knowledge/syntheses/synthesis_{date}.md

  Domains:
    {domain 1}: {N} papers — {one-line trend}
    {domain 2}: {N} papers — {one-line trend}
    ...

  Top insight: {most important cross-domain finding}
  Top opportunity: {highest priority research gap}
```

---

## Incremental Synthesis (Subsequent Runs)

When running `/synthesize` after the first time:

1. **Check for existing domain syntheses** in `knowledge/syntheses/domain_*.md`
2. **If no `- full` flag**: Only re-synthesize domains that have new inbox papers. Domains with no new papers keep their existing domain synthesis.
3. **If `- full` flag**: Delete all domain syntheses and re-synthesize from scratch.
4. **Cross-domain synthesis is always regenerated** (it must reflect the current state of all domain syntheses).

For domains with new papers:
- Read the new .tex sources + re-read the existing domain synthesis
- Update the domain synthesis to incorporate the new papers
- The new papers may create new threads, resolve existing tensions, or open new gaps

---

## Key Rules

- **PDF IS BANNED.** Never download or link to PDF files.
- **NOTES ALONE ARE INSUFFICIENT.** Per-domain analysis MUST read .tex source. Summary notes are for classification and cross-referencing only. The depth of insight is directly proportional to how much original source you read.
- **Two-phase pipeline is mandatory.** Phase 1 (per-domain from .tex) then Phase 2 (cross-domain from domain syntheses). Never skip Phase 1.
- **The synthesis must be grounded in evidence** from the actual .tex source. Every claim should reference which paper(s) support it, ideally with specific sections, equations, or experimental results. No unsupported speculation.
- **Never overwrite paper notes** (`knowledge/summary_*.md`). Only write to `knowledge/syntheses/`.
- When `- full` is specified, rebuild everything from scratch — don't carry over insights from previous syntheses without re-deriving them.
- Classification into domains is judgment-based — when uncertain, assign both primary and secondary domains.
- New domains can emerge. If a paper doesn't fit existing domains, create a new one and explain why.
- Always distinguish between what papers actually show vs. what they claim. Flag overclaimed results.
- When papers contradict each other, present both sides and analyze why (different setups? different metrics? different assumptions?).
- If there's only 1 paper in a domain, still analyze it but note that cross-paper insights are limited.
- Daily paper lists in `knowledge/daily/` provide context on what was available but not read — reference them in gap analysis.
- **Shallow synthesis is a failure mode.** If a domain analysis could have been produced from the abstract alone, it's not deep enough. The value of reading .tex source is in extracting methodological details, experimental nuances, and implicit assumptions that aren't visible in abstracts or summaries.
