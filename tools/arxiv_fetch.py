#!/usr/bin/env python3
"""arXiv fetcher: search papers and download LaTeX source (.tar.gz).

NEVER downloads PDF. Only fetches metadata and LaTeX source archives.
"""

import argparse
import json
import pathlib
import sys
import tarfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

NS = "http://www.w3.org/2005/Atom"
ARXIV_API = "http://export.arxiv.org/api/query"
SOURCE_DIR_DEFAULT = "papers/inbox"


def search(query, max_results=10):
    """Search arXiv API and return structured metadata."""
    encoded = urllib.parse.quote(query)
    url = (
        f"{ARXIV_API}?search_query={encoded}"
        f"&start=0&max_results={max_results}"
        f"&sortBy=relevance&sortOrder=descending"
    )
    with urllib.request.urlopen(url, timeout=30) as r:
        root = ET.fromstring(r.read())

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

    return papers


def download_source(arxiv_id, output_dir=SOURCE_DIR_DEFAULT):
    """Download LaTeX source (.tar.gz) and extract to output_dir/arxiv_id/."""
    out_path = pathlib.Path(output_dir) / arxiv_id
    source_url = f"https://arxiv.org/e-print/{arxiv_id}"

    if out_path.exists() and any(out_path.iterdir()):
        print(f"Already exists: {out_path}/")
        return str(out_path)

    out_path.mkdir(parents=True, exist_ok=True)
    tar_path = out_path / "source.tar.gz"

    req = urllib.request.Request(source_url)
    req.add_header("User-Agent", "arxiv-skill/1.0")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"No LaTeX source available for {arxiv_id} (scanned/older paper)")
            try:
                out_path.rmdir()
            except OSError:
                pass
            return None
        raise

    if len(data) < 1024:
        print(f"Warning: source file suspiciously small ({len(data)} bytes)")
        try:
            out_path.rmdir()
        except OSError:
            pass
        return None

    tar_path.write_bytes(data)
    print(f"Downloaded: {tar_path} ({len(data) // 1024} KB)")

    # Extract
    try:
        with tarfile.open(tar_path, "r:gz") as tf:
            members = [
                m for m in tf.getmembers()
                if not m.name.startswith("/") and ".." not in m.name
            ]
            tf.extractall(path=out_path, members=members)
        print(f"Extracted to: {out_path}/")

        tex_files = list(out_path.rglob("*.tex"))
        if tex_files:
            print(f"Found {len(tex_files)} .tex file(s):")
            for f in sorted(tex_files):
                rel = f.relative_to(out_path)
                lines = f.read_text(errors="replace").count("\n")
                print(f"  {rel} ({lines} lines)")
        else:
            print("No .tex files found — source may use different format")

    except tarfile.TarError:
        # Not gzip tar — might be single .tex file
        content = tar_path.read_bytes()
        try:
            text = content.decode("utf-8", errors="replace")
            tex_path = out_path / "main.tex"
            tex_path.write_text(text)
            print(f"Saved as plain text: {tex_path}")
        except Exception:
            print("Could not extract source: unrecognized format")

    return str(out_path)


def fetch_paper(arxiv_id):
    """Fetch metadata for a single paper by ID."""
    url = f"{ARXIV_API}?id_list={arxiv_id}"
    with urllib.request.urlopen(url, timeout=30) as r:
        root = ET.fromstring(r.read())

    entries = root.findall(f"{{{NS}}}entry")
    if not entries:
        print(f"Paper not found: {arxiv_id}")
        return None

    entry = entries[0]
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

    return {
        "id": aid,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "published": published,
        "categories": cats,
        "abs_url": f"https://arxiv.org/abs/{aid}",
        "source_url": f"https://arxiv.org/e-print/{aid}",
    }


def main():
    parser = argparse.ArgumentParser(
        description="arXiv paper search and LaTeX source download"
    )
    sub = parser.add_subparsers(dest="command")

    s = sub.add_parser("search", help="Search arXiv")
    s.add_argument("query", help="Search query or 'id:ARXIV_ID'")
    s.add_argument("--max", type=int, default=10, dest="max_results")

    d = sub.add_parser("download", help="Download LaTeX source")
    d.add_argument("arxiv_id", help="arXiv ID (e.g. 2301.07041)")
    d.add_argument("--dir", default=SOURCE_DIR_DEFAULT, dest="output_dir")

    f = sub.add_parser("paper", help="Fetch single paper metadata")
    f.add_argument("arxiv_id", help="arXiv ID")

    args = parser.parse_args()

    if args.command == "search":
        results = search(args.query, args.max_results)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif args.command == "download":
        result = download_source(args.arxiv_id, args.output_dir)
        if result is None:
            sys.exit(1)

    elif args.command == "paper":
        result = fetch_paper(args.arxiv_id)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
