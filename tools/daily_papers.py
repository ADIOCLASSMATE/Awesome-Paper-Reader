#!/usr/bin/env python3
"""Daily LLM Papers: Fetch and filter today's LLM papers from arXiv.

Only fetches arXiv categories relevant to LLM research.
Scores papers by LLM relevance and excludes non-LLM topics.
Uses OpenAlex (free, no API key) for author quality and institution lookup.
"""

import argparse
import json
import ssl
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# SSL context that handles arXiv's sometimes-tricky TLS
_SSL_CTX = ssl.create_default_context()

NS = "http://www.w3.org/2005/Atom"
ARXIV_API = "http://export.arxiv.org/api/query"
OPENALEX_API = "https://api.openalex.org"

# ── LLM relevance scoring ──────────────────────────────────────────

INCLUDE = {
    2: [  # Core LLM topics — algorithm/model level
        "large language model", " llm ", "llm-", "gpt-4", "chatgpt",
        "rlhf", "dpo ", "direct preference", "reward model",
        "chain-of-thought", "reasoning model", " o1 ", " o3 ",
        "scaling law", "compute-optimal",
        "in-context learning", "few-shot",
        "fine-tun", "instruction tun", "supervised fine-tun",
        "hallucinat", "factuality",
        "deepseek", "qwen", "llama", "gemini", "claude",
        "reinforcement learn from human",
        "o1-like", "deepseek-r1", "deepseek-v",
        # Architecture / pretraining / data — user's primary interest
        "pretrain data", "data mix", "synthetic data", "data quality",
        "mixture of expert", " moe ", "attention mechanism",
        "tokeniz", "embedding model", "positional encod",
        "model architecture", "architecture design",
        "language model pretrain",
        "rlvr", "verifiable reward",
    ],
    1: [  # LLM-adjacent — still interesting
        "transformer", "quantiz", "pruning", "distillation", "speculative decod",
        "retrieval-augment", " rag ", "long context",
        "code generat", "program synthesis",
        "multimodal", "vision-language", "vlm",
        "safety", "jailbreak", "red-team",
        "prompt", "instruction follow",
        "math reason", "code reason", "world model",
        "alignment", "value alignment",
        "KV cache", "kv-cache",
        "language model",
        "pretrain", "self-supervis",
        # Agent — secondary interest
        "agent", "tool use", "function call",
    ],
    0.5: [  # Tangentially related
        "nlp", "natural language",
        "text generat",
        "benchmark", "evaluat",
    ],
}

EXCLUDE = {
    3: [  # Strong exclude — clearly not LLM
        "object detect", "instance segment", "semantic segment",
        "image synthesis", "video synthesis",
        "speech recogn", "text-to-speech",
        "music generat", "audio generat", "sound generat",
        "point cloud", "3d reconstruct",
        "medical image", "x-ray", " mri ",
        "protein", "drug discover", "molecular",
        "manipulation task", "grasp", "robot arm",
        "autonomous driv", "lidar",
        "wireless", "channel estimat",
        "recommender system",
        "face recogn", "emotion recogn",
        "super resolution", "deblurr", "denois",
        "style transfer",
        "graph neural", " gnn ",
        "federated learn",
        "compressive sens",
        # Application domains — LLM is just a tool, not the contribution
        "ancient chinese", "character recognition",
        "physics olympiad", "physics simulat",
        "investment bank", "trading strategy",
        "depression detect", "mental health detect",
        "digital health", "clinical decision",
        "blast-induced", "structural health monitor",
        "gesture predict", "robot co-speech",
        "chinese art", "art understand",
        "legal case", "legal reason", "legal judgment",
        "cyber threat intellig", "threat intellig",
        "aesthetic assess",
        "knowledge graph construct", "kg-complet",
    ],
    1: [  # Mild exclude — probably not core LLM algorithm work
        "diffusion model", "gan ", "generative adversarial",
        "image generat", "video generat",
        "video diffusion",
        "vision-language model", "vlm",
        "multimodal large language model",
        "world model",
        "driving coach",
        # Pure agent application papers (not algorithmic contribution)
        "web navigation agent", "gui agent",
        "software engineer agent",
        "autonomous agent", "embodied agent",
    ],
}

# ── Institution tiers ───────────────────────────────────────────────

TIER1 = [
    "openai", "deepmind", "anthropic", "meta fair", "meta ai",
    "facebook ai", "google research", "google brain",
    "microsoft research", "apple machine learning", "nvidia research",
    "amazon agi", "hugging face", "xai", "x.ai",
    "mistral", "cohere", "ai21",
    # US
    "mit ", "stanford", "carnegie mellon", "cmu ",
    "berkeley", "uc berkeley", "princeton", "harvard",
    "caltech", "cornell", "columbia university",
    "university of washington", "umich", "university of michigan",
    "georgia tech", "uiuc", "university of illinois",
    "ucla", "ut austin", "university of texas",
    "umd", "university of maryland", "upenn",
    "nyu", "yale", "brown university",
    # International
    "eth zurich", "epfl", "oxford", "cambridge",
    "university of toronto", "mila", "inria", "max planck",
    "allen institute", "ai2",
    # China
    "tsinghua", "peking university", "pku",
]

TIER2 = [
    "shanghai jiao tong", "sjtu", "zhejiang university",
    "ustc", "university of science and technology",
    "fudan", "nanjing university", "beijing institute",
    "harbin institute", "tongji", "beihang", "renmin",
    "south china university", "sun yat-sen",
    "hkust", "hku", "chinese university of hong kong",
    "city university of hong kong",
    "chinese academy of sciences",
    "alibaba", "bytedance", "tencent", "baidu", "huawei",
    "shanghai ai lab", "shanghai artificial intelligence",
    "beijing academy of artificial intelligence",
    "samsung research", "ibm research", "intel labs",
    "salesforce research", "adobe research",
    "purdue", "ohio state", "penn state", "rice university",
    "northwestern", "usc ", "university of southern california",
    "university of california", "ucsd", "uc davis",
    "kaist", "nus ", "university of tokyo",
]


def compute_relevance(title, abstract):
    """Score paper relevance to LLM research.

    Uses per-tier hit capping to prevent keyword stacking.
    The score measures how centrally a paper is about LLMs,
    not how many LLM-related terms it happens to mention.
    """
    text = (title + " " + abstract).lower()

    # Title gets boosted — keywords in title indicate centrality
    title_lower = title.lower()

    # Collect positive scores with per-tier caps
    pos = 0.0
    for weight, keywords in INCLUDE.items():
        hits = 0
        cap = 1  # Only count 1 hit per tier (not stacking)
        for kw in keywords:
            if kw in text:
                pos += weight
                hits += 1
                if hits >= cap:
                    break

    # Boost for core LLM keywords appearing in the title (strong signal)
    core_in_title = any(kw in title_lower for kw in INCLUDE.get(2, []))
    if core_in_title:
        pos += 1.5  # Title mention = the paper is ABOUT this topic

    # Extra boost for algorithm/architecture/data keywords in title
    # These are the user's primary interest areas
    ALGO_TITLE_KEYWORDS = [
        "pretrain", "architecture", "scaling law", "data mix",
        "mixture of expert", " moe ", "attention", "tokeniz",
        "fine-tun", "rlhf", "dpo", "rlvr", "alignment",
        "distillation", "pruning", "quantiz",
        "language model",
    ]
    if any(kw in title_lower for kw in ALGO_TITLE_KEYWORDS):
        pos += 1.0

    # Collect negative scores (no cap — exclusion should be strong)
    neg = 0.0
    for penalty, keywords in EXCLUDE.items():
        for kw in keywords:
            if kw in text:
                neg += penalty

    # If no positive signal at all, this is not an LLM paper
    if pos == 0:
        return 0.0

    # Strong exclude: if negatives dominate, paper is not about LLMs
    if neg >= pos:
        return 0.0

    return pos - neg


def fetch_papers(categories, max_results, since_date):
    """Fetch papers from arXiv API."""
    cat_query = " OR ".join(f"cat:{c}" for c in categories)
    url = (
        f"{ARXIV_API}?search_query={urllib.parse.quote(cat_query)}"
        f"&sortBy=submittedDate&sortOrder=descending"
        f"&max_results={max_results}"
    )

    req = urllib.request.Request(url)
    req.add_header("User-Agent", "daily-papers-skill/1.0")

    try:
        with urllib.request.urlopen(req, timeout=60, context=_SSL_CTX) as r:
            root = ET.fromstring(r.read())
    except Exception as e:
        print(f"Error fetching arXiv: {e}", file=sys.stderr)
        return []

    papers = []
    for entry in root.findall(f"{{{NS}}}entry"):
        aid = (
            entry.findtext(f"{{{NS}}}id", "")
            .split("/abs/")[-1]
            .split("v")[0]
        )
        title = (
            entry.findtext(f"{{{NS}}}title", "") or ""
        ).strip().replace("\n", " ")
        abstract = (
            entry.findtext(f"{{{NS}}}summary", "") or ""
        ).strip().replace("\n", " ")
        authors = [
            a.findtext(f"{{{NS}}}name", "")
            for a in entry.findall(f"{{{NS}}}author")
        ]
        published = entry.findtext(f"{{{NS}}}published", "")[:10]
        cats = [
            c.get("term", "")
            for c in entry.findall(f"{{{NS}}}category")
        ]

        # Date filter
        try:
            pub_date = datetime.strptime(published, "%Y-%m-%d").date()
        except ValueError:
            continue

        if pub_date < since_date:
            continue

        relevance = compute_relevance(title, abstract)

        papers.append({
            "id": aid,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "published": published,
            "categories": cats,
            "abs_url": f"https://arxiv.org/abs/{aid}",
            "source_url": f"https://arxiv.org/e-print/{aid}",
            "relevance_score": round(relevance, 1),
        })

    papers.sort(key=lambda p: p["relevance_score"], reverse=True)
    return papers


def _normalize_name(name):
    """Normalize author name for comparison: lowercase, strip accents, collapse whitespace."""
    import unicodedata
    name = unicodedata.normalize("NFKD", name.lower())
    name = "".join(c for c in name if not unicodedata.combining(c))
    return " ".join(name.split())


def check_author_openalex(author_name):
    """Look up author on OpenAlex (free, no API key). Returns dict or None.

    Uses display_name.search for exact-ish matching, then validates that
    the returned name is a reasonable match (not a completely different person).
    """
    params = urllib.parse.urlencode({
        "search": author_name,
        "per_page": 5,
        "select": "id,display_name,works_count,cited_by_count,summary_stats",
    })
    url = f"{OPENALEX_API}/authors?{params}"

    req = urllib.request.Request(url)
    req.add_header("User-Agent", "mailto:daily-papers-skill@example.com")

    try:
        with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as r:
            data = json.loads(r.read())
    except Exception:
        return None

    results = data.get("results") or []
    if not results:
        return None

    # Pick the best match by name similarity
    target = _normalize_name(author_name)
    best = None
    best_score = 0.0

    for a in results:
        candidate = _normalize_name(a.get("display_name", ""))
        # Exact match
        if candidate == target:
            best = a
            break
        # Last name match (most discriminative for Chinese/Korean names)
        target_parts = target.split()
        candidate_parts = candidate.split()
        if target_parts and candidate_parts and target_parts[-1] == candidate_parts[-1]:
            score = 0.7
            # First initial match bonus
            if target_parts[0][0] == candidate_parts[0][0]:
                score = 0.9
            if score > best_score:
                best_score = score
                best = a

    if not best:
        # Fallback to first result but mark as uncertain
        best = results[0]

    stats = best.get("summary_stats") or {}
    return {
        "name": best.get("display_name"),
        "paperCount": best.get("works_count", 0),
        "citationCount": best.get("cited_by_count", 0),
        "hIndex": stats.get("h_index", 0),
        "i10Index": stats.get("i10_index", 0),
        "match_confidence": "exact" if best is results[0] and _normalize_name(results[0].get("display_name", "")) == target else "approximate",
    }


def check_paper_openalex(arxiv_id):
    """Look up paper on OpenAlex by arXiv ID. Returns authorships or None."""
    # OpenAlex uses doi format: 10.48550/arXiv.XXXX.XXXXX
    doi = f"10.48550/arXiv.{arxiv_id}"
    url = f"{OPENALEX_API}/works/doi:{urllib.parse.quote(doi)}?select=authorships,cited_by_count"

    req = urllib.request.Request(url)
    req.add_header("User-Agent", "mailto:daily-papers-skill@example.com")

    try:
        with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as r:
            data = json.loads(r.read())
    except Exception:
        return None

    return data


def _classify_institution(institution_name):
    """Classify institution into tier1/tier2/unknown."""
    if not institution_name or institution_name == "unknown":
        return "unknown"
    inst_lower = institution_name.lower()
    for pattern in TIER1:
        if pattern in inst_lower:
            return "tier1"
    for pattern in TIER2:
        if pattern in inst_lower:
            return "tier2"
    return "unknown"


def enrich_with_authors(papers):
    """Add OpenAlex author quality + institution data. Free, no API key."""
    for i, paper in enumerate(papers):
        if not paper["authors"]:
            paper["author_quality"] = "unknown"
            paper["first_author_institution"] = "unknown"
            paper["first_author_institution_tier"] = "unknown"
            paper["first_author_openalex"] = None
            paper["paper_citations_openalex"] = None
            continue

        first_author = paper["authors"][0]

        # Try paper-level lookup first (most accurate for institutions)
        oa_paper = check_paper_openalex(paper["id"])
        institution = "unknown"
        inst_tier = "unknown"
        paper_citations = None

        if oa_paper:
            paper_citations = oa_paper.get("cited_by_count")
            authorships = oa_paper.get("authorships") or []
            for a in authorships:
                oa_name = _normalize_name(
                    a.get("author", {}).get("display_name", "")
                )
                if oa_name == _normalize_name(first_author):
                    insts = a.get("institutions") or []
                    if insts:
                        institution = insts[0].get("display_name", "unknown")
                        inst_tier = _classify_institution(institution)
                    # Also get author OpenAlex ID for more reliable profile lookup
                    oa_author_id = a.get("author", {}).get("id")
                    if oa_author_id:
                        # Fetch author profile by ID (exact match)
                        try:
                            req = urllib.request.Request(oa_author_id)
                            req.add_header("User-Agent", "mailto:daily-papers-skill@example.com")
                            with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as r:
                                adata = json.loads(r.read())
                            stats = adata.get("summary_stats") or {}
                            oa_author = {
                                "name": adata.get("display_name"),
                                "paperCount": adata.get("works_count", 0),
                                "citationCount": adata.get("cited_by_count", 0),
                                "hIndex": stats.get("h_index", 0),
                                "i10Index": stats.get("i10_index", 0),
                                "match_confidence": "exact",
                            }
                            paper["first_author_openalex"] = oa_author
                        except Exception:
                            pass
                    break

        # Fallback: author profile lookup by name search
        if paper.get("first_author_openalex") is None:
            oa_author = check_author_openalex(first_author)
            paper["first_author_openalex"] = oa_author

        paper["first_author_institution"] = institution
        paper["first_author_institution_tier"] = inst_tier
        paper["paper_citations_openalex"] = paper_citations

        oa_author = paper.get("first_author_openalex")
        if oa_author:
            h = oa_author.get("hIndex", 0) or 0
            c = oa_author.get("citationCount", 0) or 0
            confidence = oa_author.get("match_confidence", "approximate")

            # If match is approximate, be more conservative
            if confidence == "approximate":
                h = h * 0.5
                c = c * 0.5

            if h >= 20 or c >= 5000:
                paper["author_quality"] = "high"
            elif h >= 10 or c >= 1000:
                paper["author_quality"] = "medium"
            elif c >= 100:
                paper["author_quality"] = "low"
            else:
                paper["author_quality"] = "unknown"
        else:
            paper["author_quality"] = "unknown"

        # OpenAlex is less strict on rate limits than S2, but still be nice
        if i < len(papers) - 1:
            time.sleep(0.3)

    return papers


def main():
    parser = argparse.ArgumentParser(
        description="Daily LLM Papers: fetch and filter from arXiv"
    )
    parser.add_argument(
        "command",
        choices=["fetch", "run"],
        help="fetch=raw papers, run=fetch+filter+score",
    )
    parser.add_argument(
        "--date", default=None,
        help="Date YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--categories", default="cs.CL,cs.AI,cs.LG",
        help="arXiv categories (comma-separated)",
    )
    parser.add_argument(
        "--max", type=int, default=150,
        dest="max_results",
        help="Max papers to fetch from arXiv",
    )
    parser.add_argument(
        "--min-score", type=float, default=0.5,
        help="Minimum relevance score to include",
    )
    parser.add_argument(
        "--check-authors", action="store_true",
        help="Look up first author on OpenAlex (free, no API key needed)",
    )

    args = parser.parse_args()

    if args.date:
        since = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        since = datetime.now().date() - timedelta(days=1)

    categories = [c.strip() for c in args.categories.split(",")]

    papers = fetch_papers(categories, args.max_results, since)

    if args.command == "fetch":
        print(json.dumps(papers, ensure_ascii=False, indent=2))
        return

    # Run: filter + score
    filtered = [p for p in papers if p["relevance_score"] >= args.min_score]

    if args.check_authors:
        filtered = enrich_with_authors(filtered)

    # Tier assignment
    for p in filtered:
        score = p["relevance_score"]
        if score >= 4:
            p["tier"] = "MUST_READ"
        elif score >= 2.5:
            p["tier"] = "INTERESTING"
        elif score >= 1:
            p["tier"] = "MARGINAL"
        else:
            p["tier"] = "SKIP"

    output = {
        "date": str(since),
        "categories": categories,
        "total_fetched": len(papers),
        "total_filtered": len(filtered),
        "papers": filtered,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
