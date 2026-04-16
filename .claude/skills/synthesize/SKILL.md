---
name: synthesize
description: Synthesize insights across all read papers. Reads every note in knowledge/, classifies papers into research domains, produces detailed per-domain analysis with trends, gaps, and cross-paper insights. Supports full re-synthesis from scratch. Use when user says "synthesize", "summarize all papers", "what insights", "organize my readings", "research trends", or "give me an overview".
argument-hint: [domain-or-empty-for-all]
allowed-tools: Bash(*), Read, Grep, Glob, Write
---

# Synthesize — Cross-Paper Insight Formation

Synthesize: $ARGUMENTS

> **CRITICAL RULE: PDF IS BANNED.** This skill only reads from local knowledge notes and .tex source.
> It does not download or access any external resources.

## Constants

- **KNOWLEDGE_DIR** — `knowledge/` relative to project root. Contains notes in `inbox/` and `archive/`.
- **DAILY_DIR** — `knowledge/daily/` relative to project root. Contains daily paper lists.
- **PAPERS_DIR** — `papers/` relative to project root. Contains LaTeX source in `inbox/` and `archive/`.
- **OUTPUT_DIR** — `knowledge/syntheses/` relative to project root. Synthesis outputs go here.

## Dual-Zone Architecture

Papers and notes follow a lifecycle:

```
/read-paper → papers/inbox/{id}/ + knowledge/inbox/summary_{tag}.md   (new, unorganized)
/synthesize → papers/archive/{domain}/{id}/ + knowledge/archive/summary_{tag}.md  (classified, cross-analyzed)
```

- **inbox/** = newly read papers, not yet synthesized into insights
- **archive/** = papers that have been classified by domain and cross-analyzed

When synthesizing:
1. Read notes from BOTH `knowledge/inbox/` AND `knowledge/archive/` (archive provides established context)
2. After synthesis, move inbox papers/notes to archive (classified by domain)
3. Papers already in archive stay in place

> Overrides (append to arguments):
> - `/synthesize` — synthesize across all papers (default)
> - `/synthesize agent` — focus on a specific domain only
> - `/synthesize - full` — force complete re-synthesis, ignore cached synthesis
> - `/synthesize - since: 2026-04-01` — only include papers read after this date
> - `/synthesize - depth: deep` — extremely detailed analysis (slower, more tokens)
> - `/synthesize - depth: quick` — brief overview (faster)

## Workflow

### Step 1: Parse Arguments

Parse `$ARGUMENTS` for:

- **Domain filter**: optional — only synthesize papers in a given research domain (e.g. "agent", "reasoning", "safety")
- **`- full`**: force complete re-synthesis from scratch, delete any previous synthesis files
- **`- since: DATE`**: only include papers whose note date is on or after DATE (YYYY-MM-DD)
- **`- depth: LEVEL`**: `quick` (brief overview) / `normal` (default) / `deep` (exhaustive analysis)

### Step 2: Collect All Notes

Scan both inbox and archive for paper notes:

```bash
# Inbox — newly read, not yet synthesized
find knowledge/inbox/ -name "summary_*.md" | sort

# Archive — previously synthesized
find knowledge/archive/ -name "summary_*.md" | sort
```

For each note, read the full content using the Read tool.

Also scan `knowledge/daily/` for daily paper lists:

```bash
find knowledge/daily/ -name "*.md" | sort
```

**If no notes exist in either inbox or archive**: Report that there are no read papers to synthesize. Suggest running `/daily-papers` and `/read-paper` first.

**Track which notes come from inbox vs archive** — this is important for Step 7 (archiving).

### Step 3: Classify Papers by Research Domain

Read every note fully. For each paper, determine its primary and secondary research domains.

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

For each paper, assign:
- **Primary domain**: the domain where the paper makes its main contribution
- **Secondary domains**: any other domains the paper touches
- **Key contribution type**: `novel_method` / `new_benchmark` / `empirical_study` / `theoretical` / `framework` / `analysis`

Build a classification table:

```text
| Paper | Tag | Primary Domain | Secondary | Contribution Type |
|-------|-----|---------------|-----------|-------------------|
```

### Step 4: Per-Domain Deep Analysis

For each domain that has papers, produce a **detailed analysis**. The depth depends on the `- depth` flag.

#### Normal depth analysis (default):

**Domain: {Domain Name}**

**Paper Landscape**:
- List all papers in this domain with their one-line core contribution
- Identify which papers are complementary vs. competing approaches

**Technical Thread**:
- Trace the evolution of ideas: what problem did each paper solve that the previous couldn't?
- Identify shared assumptions across papers and whether they hold
- Map methodological connections: which papers build on which?

**Key Findings**:
- Aggregate the most important results across papers
- Note where papers agree or contradict each other
- Highlight surprising or counter-intuitive results

**Open Gaps**:
- What problems are mentioned but not solved?
- What assumptions remain unchallenged?
- What combinations of ideas from different papers haven't been tried?

**Research Trends**:
- Is this area heating up or cooling down?
- What direction are the latest papers pushing?
- What's the community converging on vs. still debating?

#### Deep depth adds:
- Full methodological comparison table (approach, assumptions, limitations, scale)
- Detailed equation-level connections between papers
- Reproducibility assessment for each paper
- Concrete research proposal for each identified gap with experimental design sketch

#### Quick depth reduces to:
- Bullet list of papers with one-sentence contribution
- 2-3 sentence trend summary
- 1-2 identified gaps

### Step 5: Cross-Domain Synthesis

After per-domain analysis, step back and look across domains:

**Convergent Threads**: Where are different domains converging on similar ideas?
- Example: "Both agent safety and reasoning research are moving toward test-time verification mechanisms"

**Divergent Approaches**: Where are similar problems being tackled with fundamentally different approaches?
- Example: "Scaling reasoning via search (Tree-of-Thought) vs. via training (RL on CoT) — different bets on compute allocation"

**Underexplored Intersections**: What combinations of domains have potential but few papers?
- Example: "Agent + Efficiency: how to make tool-augmented agents faster without losing capability"

**Meta-Observations**: Patterns across the entire reading corpus
- What methodologies are becoming standard?
- What evaluation practices need improvement?
- What assumptions does the field take for granted that might be wrong?

### Step 6: Research Opportunity Map

Produce a prioritized list of research opportunities:

```text
| Priority | Opportunity | Domain(s) | Evidence | Feasibility |
|----------|------------|-----------|----------|-------------|
| HIGH  | {description} | {domains} | {which papers/gaps} | {assessment} |
| MEDIUM | {description} | {domains} | {which papers/gaps} | {assessment} |
| LOW   | {description} | {domains} | {which papers/gaps} | {assessment} |
```

Criteria for priority:
- **HIGH**: Multiple papers point to the gap, solution seems tractable, high impact potential
- **MEDIUM**: Gap identified but solution unclear, or single paper points to it
- **LOW**: Speculative, requires significant resources, or unclear impact

### Step 7: Archive Inbox Papers

After producing the synthesis, **move all inbox papers and notes to the archive**, organized by domain.

For each paper that was in `knowledge/inbox/`:

1. **Determine its domain** from the classification in Step 3
2. **Move the knowledge note** from `knowledge/inbox/summary_{tag}.md` to `knowledge/archive/summary_{tag}.md`
3. **Move the .tex source** from `papers/inbox/{id}/` to `papers/archive/{domain}/{id}/`
   - Create the domain directory if it doesn't exist: `mkdir -p papers/archive/{domain}`
   - Domain directory names use snake_case: `safety_alignment`, `training_scaling`, `reasoning`, `architecture`, `efficiency`, `multimodal`, `retrieval_rag`, `evaluation`, `data_synthesis`, `agent`

Example:
```bash
# Note: from inbox to archive
mv knowledge/inbox/summary_agent_security.md knowledge/archive/summary_agent_security.md

# Source: from inbox to domain-organized archive
mkdir -p papers/archive/safety_alignment
mv papers/inbox/2604.11790 papers/archive/safety_alignment/
```

**Papers already in archive are NOT moved** — they stay in their existing domain directory.

After archiving, verify:
- `knowledge/inbox/` should be empty (or contain only notes that were not part of this synthesis)
- `papers/inbox/` should be empty (or contain only papers that were not part of this synthesis)
- `knowledge/archive/` contains all synthesized notes
- `papers/archive/{domain}/` contains all synthesized .tex sources

### Step 8: Save Synthesis Output

Save to `knowledge/syntheses/synthesis_{date}.md`:

```
knowledge/syntheses/synthesis_2026-04-14.md
```

**If `- full` is specified**, delete any previous synthesis files in `knowledge/syntheses/` before writing (fresh start).

**Output format**:

```markdown
# Research Synthesis — {date}

- **Papers analyzed**: {N}
- **Domains identified**: {N}
- **Date range**: {earliest} to {latest}
- **Depth**: {quick/normal/deep}

## Classification

| Paper | Tag | Primary Domain | Secondary | Type |
|-------|-----|---------------|-----------|------|
{table}

---

## Domain Analyses

### {Domain 1}

{full per-domain analysis from Step 4}

### {Domain 2}

{full per-domain analysis from Step 4}

---

## Cross-Domain Synthesis

{from Step 5}

---

## Research Opportunity Map

{from Step 6}

---

## Reading Recommendations

Based on the current synthesis, suggest next papers to read:

### Fill gaps in existing domains
- {paper suggestion} — would clarify {gap}

### Expand into new domains
- {domain suggestion} — currently underrepresented in readings

### Follow citation trails
- {paper} cited in {read paper} looks important because {reason}

---

*Generated by synthesize skill*
*Next: /daily-papers to discover more, /read-paper ID to read specific papers*
```

### Step 8: Report

Present a concise summary to the user:

```text
Synthesized {N} papers across {M} domains
  Output: knowledge/syntheses/synthesis_{date}.md

  Domains:
    {domain 1}: {N} papers — {one-line trend}
    {domain 2}: {N} papers — {one-line trend}
    ...

  Top insight: {most important cross-domain finding}
  Top opportunity: {highest priority research gap}
```

## Key Rules

- **PDF IS BANNED.** Never download or link to PDF files.
- **Read ALL notes fully** before synthesizing. Shallow reading leads to shallow synthesis.
- The synthesis must be **grounded in evidence** from the actual paper notes. Every claim should reference which paper(s) support it. No unsupported speculation.
- **Never overwrite paper notes** (`knowledge/summary_*.md`). Only write to `knowledge/syntheses/`.
- When `- full` is specified, rebuild everything from scratch — don't carry over insights from previous syntheses without re-deriving them.
- Classification into domains is judgment-based — when uncertain, assign both primary and secondary domains.
- New domains can emerge. If a paper doesn't fit existing domains, create a new one and explain why.
- The "Connections" section in each paper note is the primary input for cross-paper linking — use it heavily.
- Always distinguish between what papers actually show vs. what they claim. Flag overclaimed results.
- When papers contradict each other, present both sides and analyze why (different setups? different metrics? different assumptions?).
- If there's only 1 paper in a domain, still analyze it but note that cross-paper insights are limited.
- Daily paper lists in `knowledge/daily/` provide context on what was available but not read — reference them in gap analysis.
