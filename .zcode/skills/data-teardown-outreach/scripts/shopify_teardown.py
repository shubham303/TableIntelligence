#!/usr/bin/env python3
"""
Deterministic Shopify catalog teardown.

Pulls a store's PUBLIC catalog from /products.json and computes teardown findings
IN CODE (never eyeballed by an LLM). The LLM's job is only to phrase these numbers
into a report/email — it must not invent or restate figures.

Usage:
    python shopify_teardown.py https://www.example.com
    python shopify_teardown.py example.com --json     # machine-readable output

Findings computed:
    - scale (products vs variants; format-fragmentation signal)
    - price bands + gaps in the price ladder
    - sold-out-but-still-listed products (lost intent)
    - launch cadence by year (catalog freshness)
    - product-type and tag concentration

Notes:
    - Some stores disable /products.json (404) — the script reports that cleanly.
    - Be polite: it paginates with a delay and a plain User-Agent.
    - This is PUBLIC catalog data only. It says nothing about actual sales/revenue —
      every finding is a hypothesis to confirm with the client's real data.
"""

import sys
import json
import time
import statistics
from collections import Counter

try:
    import requests
except ImportError:
    sys.exit("Install requests first:  pip install requests")

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CatalogResearch/1.0)"}


def normalize(url: str) -> str:
    url = url.strip().rstrip("/")
    if not url.startswith("http"):
        url = "https://" + url
    return url


def pull_catalog(base_url: str, delay: float = 1.2):
    """Paginate /products.json and return the full product list (or raise)."""
    products, page = [], 1
    while True:
        u = f"{base_url}/products.json?limit=250&page={page}"
        r = requests.get(u, headers=HEADERS, timeout=30)
        if r.status_code == 404:
            raise RuntimeError("This store has disabled /products.json (404). "
                               "Fall back to scraping /collections/all or a research tool.")
        if r.status_code != 200:
            raise RuntimeError(f"Got HTTP {r.status_code} from {u}")
        batch = r.json().get("products", [])
        if not batch:
            break
        products.extend(batch)
        page += 1
        time.sleep(delay)
    if not products:
        raise RuntimeError("No products returned — store may be empty or password-protected.")
    return products


def analyze(products: list) -> dict:
    """Compute all findings deterministically. Returns a dict of numbers/tables."""
    rows, variants = [], []
    for p in products:
        vs = p.get("variants", []) or []
        prices = [float(v["price"]) for v in vs if v.get("price") not in (None, "")]
        avail = [bool(v.get("available")) for v in vs]
        rows.append({
            "title": p.get("title"),
            "type": p.get("product_type") or "(none)",
            "tags": p.get("tags") or [],
            "created": (p.get("created_at") or "")[:4],
            "min_price": min(prices) if prices else None,
            "all_sold_out": (len(avail) > 0 and not any(avail)),
        })
        for v in vs:
            variants.append({
                "price": float(v["price"]) if v.get("price") not in (None, "") else None,
                "available": bool(v.get("available")),
            })

    n_prod, n_var = len(rows), len(variants)
    prices = [v["price"] for v in variants if v["price"] is not None]

    # price bands
    bands = Counter()
    for pr in prices:
        if pr < 30:      bands["<$30"] += 1
        elif pr < 60:    bands["$30-59"] += 1
        elif pr < 100:   bands["$60-99"] += 1
        elif pr < 150:   bands["$100-149"] += 1
        elif pr < 250:   bands["$150-249"] += 1
        else:            bands["$250+"] += 1
    band_order = ["<$30", "$30-59", "$60-99", "$100-149", "$150-249", "$250+"]

    sold_out = [r["title"] for r in rows if r["all_sold_out"]]
    launch = Counter(r["created"] for r in rows if r["created"])
    types = Counter(r["type"] for r in rows)
    tags = Counter(t for r in rows for t in r["tags"])

    # crude "price ladder gap" detector: any adjacent middle band that is
    # near-empty while both a lower and higher band are well populated.
    gap_note = None
    mids = [("$60-99", bands["$60-99"]), ("$100-149", bands["$100-149"])]
    low_pop = bands["<$30"] + bands["$30-59"]
    high_pop = bands["$150-249"] + bands["$250+"]
    mid_pop = sum(c for _, c in mids)
    if prices and low_pop > 0 and high_pop > 0 and mid_pop <= max(1, 0.1 * n_var):
        gap_note = ("Price ladder gap: prices cluster low and high with a near-empty "
                    "$60-149 middle — a spot where the 'not ready for the top tier' "
                    "buyer often drops off.")

    return {
        "scale": {
            "products": n_prod,
            "variants": n_var,
            "avg_variants_per_product": round(n_var / n_prod, 2) if n_prod else 0,
            "fragmentation_signal": (n_var / n_prod < 1.1) if n_prod else False,
        },
        "price": {
            "min": min(prices) if prices else None,
            "median": statistics.median(prices) if prices else None,
            "mean": round(statistics.mean(prices), 2) if prices else None,
            "max": max(prices) if prices else None,
            "bands": {b: bands[b] for b in band_order},
            "gap_note": gap_note,
        },
        "availability": {
            "sold_out_but_listed_count": len(sold_out),
            "sold_out_examples": sold_out[:10],
        },
        "launch_cadence": dict(sorted(launch.items())),
        "product_types": dict(types.most_common(10)),
        "top_tags": dict(tags.most_common(15)),
        "unique_tags": len(tags),
    }


def print_report(store: str, a: dict):
    s, pr = a["scale"], a["price"]
    print(f"\n=== TEARDOWN: {store} ===")
    print(f"Products: {s['products']} | Variants: {s['variants']} "
          f"| avg variants/product: {s['avg_variants_per_product']}")
    if s["fragmentation_signal"]:
        print("  → FRAGMENTATION SIGNAL: ~1 variant per product. The catalog is likely "
              "split by format/size into separate products instead of variants of one "
              "product (hurts the buying path + SEO).")

    print(f"\nPrice (USD): min {pr['min']} | median {pr['median']} "
          f"| mean {pr['mean']} | max {pr['max']}")
    print("  bands:", pr["bands"])
    if pr["gap_note"]:
        print("  →", pr["gap_note"])

    av = a["availability"]
    print(f"\nSold out but still listed: {av['sold_out_but_listed_count']}")
    for t in av["sold_out_examples"]:
        print("   -", t)

    print("\nLaunch cadence (by year):", a["launch_cadence"])
    print("Product types:", a["product_types"])
    print(f"Tag concentration ({a['unique_tags']} unique):", a["top_tags"])
    print("\nREMINDER: public catalog only — findings are hypotheses, not sales facts.")


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    as_json = "--json" in sys.argv
    if not args:
        sys.exit("Usage: python shopify_teardown.py <store-url> [--json]")
    store = normalize(args[0])
    try:
        products = pull_catalog(store)
    except Exception as e:
        sys.exit(f"ERROR: {e}")
    result = analyze(products)
    if as_json:
        print(json.dumps({"store": store, "findings": result}, indent=2))
    else:
        print_report(store, result)


if __name__ == "__main__":
    main()
