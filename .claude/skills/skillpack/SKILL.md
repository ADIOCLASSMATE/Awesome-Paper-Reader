---
name: skillpack
description: >-
  Skill pack manager: discover and integrate external skills (Personalize),
  curate the skillpack registry (Registry), and create new skills from scratch
  (Create). Self-learning is handled by ECC's continuous-learning-v2 (global,
  hook-based, confidence-scored). This skill only covers what ECC cannot do:
  external skill discovery, compatibility analysis, registry curation, and
  skill creation. Never edits SKILL.md directly — all changes go through
  skill-creator's draft→test→iterate loop, human merges.
  Trigger phrases: "personalize my skills", "integrate this skill", "update
  skillpack", "find a skill for", "create a skill", "improve skill", "refresh
  the skillpack registry", "assess this skill pack", "update
  skill_dictionary.yaml", "update index.yaml".
---

# Skillpack

Three modes: **Personalize** (discover and integrate external skills), **Registry** (curate `skillpacks/skill_dictionary.yaml` and presets), **Create** (build a new skill from scratch).

> **Note:** Session-mode lesson extraction is NOT included in this edition. Self-learning, instinct observation, confidence scoring, and instinct-to-skill evolution are handled by ECC's `continuous-learning-v2` skill (global, hook-based, 100% observation coverage, project-scoped instincts). This skill focuses exclusively on capabilities ECC does not provide: external skill discovery, compatibility analysis, registry curation, and de-novo skill creation.

Skill creation and significant rewrites always go through `skill-creator` — never write to SKILL.md directly.

If `skill-creator` is unavailable in the current environment, stop and tell the user. Do not silently simulate its workflow.

---

## Mode 1 — Personalize

Activate when the user says "personalize", "integrate this skill", "find a skill for", or provides an external SKILL.md path or URL.

### Step 0 — Discover (if no target provided)

1. If the user gives a description rather than a path/URL, search the registry:
   ```bash
   npx skills find "<query>"
   ```
   Present the top results (name, description, install command) and ask the user which to integrate. Then continue with the chosen skill(s).

### Step 1 — Read external skill(s)

2. Read the target: a single SKILL.md, a skills directory, or a skill pack repo. Extract:
   - Name, description, trigger phrases
   - Tools, MCP servers, and external dependencies it references
   - Behavioral patterns (workflows, delegation, output files)

### Step 2 — Inventory installed skills

3. Read all SKILL.md files in the project `.claude/skills/`. Build a map of:
   - Names and descriptions
   - Tools and MCP servers already in use
   - Overlapping trigger phrases

### Step 3 — Analyze

4. For each external skill, assess three dimensions:

   **Compatibility** — will it conflict?
   - Name collision with an installed skill?
   - References a tool/MCP not configured (e.g., `alpha login` not done)?
   - Contradicts a behavioral rule in an existing skill?

   **Scope overlap** — does it duplicate something?
   - Substantially the same as an installed skill → flag as overlap, note the delta
   - Partially overlapping → identify which parts are additive

   **New capability** — what does it genuinely add?
   - List capabilities not covered by any installed skill

### Step 4 — Interview the user

5. Ask targeted questions based on the analysis. Ask all at once, not one-by-one:

   For each **overlap**: > "`<external>` overlaps with your `<installed>`. It differs in: `<delta>`. Replace, merge, or skip?"

   For each **missing dependency**: > "`<external>` requires `<tool/MCP>`. Do you have it? If not, skip those parts?"

   For each **behavioral conflict**: > "`<external>` does `<X>` but your `<installed>` does `<Y>`. Which do you prefer?"

   Open: > "Anything from this skill you explicitly don't want?"

### Step 5 — Create or improve via skill-creator

6. Based on user answers, determine the scope:
   - **Additive merge** (minor additions to an existing skill) → write a unified diff to `lessons/YYYYMMDD-personalize-<slug>.diff` with a companion `.md`.
   - **New skill or substantial rewrite** → hand off to `skill-creator`: describe the desired skill, provide the source material and user's confirmed preferences as context, and follow its draft→test→iterate loop. Output lands in `lessons/` as a proposal.

7. Tell the user: *"Ready in `lessons/`. Review and apply with `git apply` when satisfied."*

---

## Mode 2 — Registry

Activate when the user asks to refresh the tracked skill-pack catalog, assess a new pack, compare packs, or update `skillpacks/skill_dictionary.yaml` / preset definitions.

### Registry inputs

Read:

- `skillpacks/skill_dictionary.yaml`
- `skillpacks/presets/*.yaml`
- `README.md` / `README_CN.md` pack comparison sections when relevant

If the user points at a new external repo, read its README and any obvious skill inventory files first.

### Responsibilities

8. Maintain `skillpacks/skill_dictionary.yaml` as the shared curated registry.

9. For each pack or skill being assessed, judge:
   - **workflow fit**
   - **gap coverage**
   - **overlap cost**
   - **dependency burden**
   - **maintenance health**
   - **composability**
   - **supervision sensitivity**
   - **autonomy bias**

10. Normalize outputs into concise labels when possible:
    - necessity: `default | recommended | optional | niche | avoid`
    - compatibility: `high | medium | low`
    - role: `base | donor | overlay | niche | experimental`

11. Recommend **subsets**, not bulk imports, unless the user clearly asks for a full-pack strategy.

12. Update presets when the registry change meaningfully affects default recommendations.

13. Keep rationales concise and decision-oriented. The registry is for recommendation and comparison, not exhaustive catalog dumps.

### Safety boundary

14. Registry curation may edit `skillpacks/skill_dictionary.yaml` and `skillpacks/presets/*.yaml`, but changes to existing `SKILL.md` behavior still require either:
    - a minor diff proposal in `lessons/`, or
    - a `skill-creator` handoff for substantial rewrites.

15. If a registry update would imply changing default project behavior materially, ask before proceeding.

---

## Mode 3 — Create

Activate when the user says "create a skill for X" or "build a new skill".

16. Capture intent: what should the skill do, when should it trigger, what's the expected output?
17. Check `npx skills find "<intent>"` — if a close match exists, suggest integrating it instead (Mode 1).
18. If creating from scratch, hand off to `skill-creator` with the captured intent. Follow its draft→test→iterate loop fully. Output lands in `lessons/` as a proposal.

---

## Constraints

- Never write directly to any `SKILL.md` file. Always propose. The human merges.
- Create `lessons/` if it does not exist.
- `skillpacks/skill_dictionary.yaml` and `skillpacks/presets/*.yaml` are curated repo metadata and may be updated directly in Registry mode when the user asks.
- All skill creation and significant rewrites go through `skill-creator`. Raw diffs are only for minor, targeted changes.
- Err toward asking rather than assuming. One unanswered question beats a wrong assumption baked into a diff.
- Self-learning is ECC's responsibility. Do not reimplement session observation, instinct extraction, or confidence scoring here.
- Do not modify any files under `~/.claude/` (global scope). All changes are project-local only.

## Example

**Personalize mode**: User says "find me a skill for LaTeX compilation" → `npx skills find "latex"` returns 3 results → user picks one → reads it, finds no conflicts → substantial enough to need skill-creator → draft→test→iterate → `lessons/20260401-personalize-latex.diff`.

**Registry mode**: User says "assess the ARIS skill pack" → read ARIS README + skill inventory → judge each skill against installed set → recommend subset → update `skill_dictionary.yaml`.

**Create mode**: User says "create a skill for summarizing paper methodology sections" → `npx skills find "methodology"` finds no close match → hand off to `skill-creator` with intent → draft→test→iterate → `lessons/20260414-create-methodology-summary.diff`.
