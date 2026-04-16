---
name: search-knowledge
description: Search across all read paper notes and syntheses in knowledge/. Find papers by topic, method, author, keyword, or insight. Use when user asks "which papers did I read about X?", "search my notes for Y", "find papers mentioning Z", or "what do I know about W?".
argument-hint: [query]
allowed-tools: Bash(*), Read, Grep, Glob
---

# Search Knowledge — Query Your Paper Reading History

Search: $ARGUMENTS

> **CRITICAL RULE: PDF IS BANNED.** This skill only reads from local knowledge notes.
> It does not download or access any external resources.

## Constants

- **KNOWLEDGE_DIR** — `knowledge/` relative to project root. Contains `summary_*.md` notes.
- **DAILY_DIR** — `knowledge/daily/` relative to project root. Contains daily paper lists.
- **SYNTHESIS_DIR** — `knowledge/syntheses/` relative to project root. Contains synthesis outputs.

## Workflow

### Step 1: Parse Arguments

The `$ARGUMENTS` is a free-form search query. Parse it to identify:

- **Keywords**: Technical terms, method names, model names (e.g., "MCP", "RLHF", "attention")
- **Authors**: Person names (e.g., "Danqi Chen", "Ashish Vaswani")
- **Domains**: Research area names (e.g., "agent", "safety", "reasoning")
- **Concepts**: Broader ideas (e.g., "test-time compute", "tool use", "injection")
- **Modifiers** (optional):
  - `- tag: TAG` — only search notes with this tag in the filename
  - `- type: notes|syntheses|daily|all` — which knowledge sources to search (default: all)
  - `- verbose` — show full matching context instead of summaries

### Step 2: Collect Knowledge Sources

Determine which sources to search based on `- type` modifier:

```bash
# Notes (default: always)
find knowledge/ -name "summary_*.md" -not -path "knowledge/syntheses/*" | sort

# Syntheses
find knowledge/syntheses/ -name "*.md" | sort

# Daily lists
find knowledge/daily/ -name "*.md" | sort
```

If `- tag: TAG` is specified, only include notes matching `summary_{TAG}.md`.

If no sources exist, report that the knowledge base is empty and suggest running `/daily-papers` and `/read-paper` first.

### Step 3: Search Across All Sources

Use Grep to search for the query terms across all collected sources. Search with multiple strategies:

1. **Exact keyword search**: Grep for the exact query terms
2. **Related term search**: Grep for semantically related terms (e.g., "injection" → also search "adversarial", "attack", "security")
3. **Author search**: If the query contains a name, search for it in author fields

For each match, capture:
- **Source file**: Which note/synthesis/daily list
- **Paper title**: From the note header
- **Match context**: The surrounding 2-3 lines showing the match
- **Section**: Which section of the note the match appears in (Problem, Method, Key Insights, Connections, etc.)

### Step 4: Organize and Rank Results

Group results by relevance:

1. **Direct matches** — query terms appear in title or core method description
2. **Method matches** — query terms appear in Method or Key Equations sections
3. **Insight matches** — query terms appear in Key Insights or Connections sections
4. **Mention matches** — query terms appear in passing (Questions, Connections)

### Step 5: Present Results

Present results in a structured format:

```text
Found {N} matches for "{query}" across {M} papers

## Papers where "{query}" is central

### {Paper Title} ({arXiv ID})
- **Tag**: {tag}
- **Why relevant**: {one-line explanation of the match}
- **Key finding**: {the most relevant insight or method detail}
- **Note**: knowledge/summary_{tag}.md

## Papers mentioning "{query}"

### {Paper Title} ({arXiv ID})
- **Context**: {where and how it mentions the query}
- **Note**: knowledge/summary_{tag}.md

## Synthesis insights

From synthesis_{date}.md:
- {relevant cross-paper finding or trend}

## Daily paper matches

From {date}.md:
- {paper title} — {tier} — {why relevant}
```

If `- verbose` is specified, include the full matching context for each result.

If no matches found, suggest:
- Alternative search terms
- Running `/daily-papers` to discover new papers on the topic
- Running `/read-paper` on specific papers to add them to the knowledge base

### Step 6: Suggest Follow-ups

Based on search results, suggest:
- Papers that could be read next (`/read-paper ID`)
- Running `/synthesize - full` if the knowledge base has grown significantly
- Running `/daily-papers` to find more papers on underrepresented topics

## Key Rules

- **PDF IS BANNED.** Never download or link to PDF files.
- **Search is local only.** Only search within `knowledge/` directory contents.
- **Be thorough.** Use multiple search strategies (exact, related, author) to avoid missing relevant papers.
- **Rank honestly.** Don't inflate relevance — distinguish between "central to the paper" and "mentioned in passing."
- **Preserve context.** Always show enough surrounding text for the user to understand why a match is relevant.
- **Report empty results clearly.** If nothing matches, say so and suggest alternatives rather than returning weak matches.
