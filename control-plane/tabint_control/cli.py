"""Admin CLI — an ENDPOINT. Depends only on services (never repositories/DB).

Local/dev administration of the control plane. In production the same services
are driven by shubham-site's web endpoints (validate-key, Stripe webhook,
account/metadata) — this CLI is the local-dev + ops equivalent.

    tabint-control init
    tabint-control mint --email you@example.com --tier trial
    tabint-control set-tier --prefix ti_AbC12345 --tier paid
    tabint-control list
    tabint-control resolve --key ti_xxx --device dev-1     # test the flow

Backend is chosen from the environment (DuckDB local / Postgres prod); override
with --db.
"""
from __future__ import annotations

import argparse
import sys

from . import security
from .db import create_provider
from .services import AdminService, EntitlementService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tabint-control", description="Control-plane admin")
    parser.add_argument("--db", help="Override DB url/path (else from environment)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Create the control-plane tables")

    p_mint = sub.add_parser("mint", help="Mint a new API key")
    p_mint.add_argument("--email", required=True)
    p_mint.add_argument("--tier", default="trial", choices=("free", "trial", "paid", "expired"))

    p_tier = sub.add_parser("set-tier", help="Change a key's tier")
    p_tier.add_argument("--prefix", required=True)
    p_tier.add_argument("--tier", required=True, choices=("free", "trial", "paid", "expired"))

    sub.add_parser("list", help="List keys")

    p_res = sub.add_parser("resolve", help="Resolve a key+device (test the flow)")
    p_res.add_argument("--key", required=True)
    p_res.add_argument("--device", default="cli-device")

    args = parser.parse_args(argv)
    provider = create_provider(args.db)
    try:
        if args.cmd == "init":
            provider.init_schema()
            print("control-plane schema ready ✓")

        elif args.cmd == "mint":
            svc = AdminService(provider.users, provider.api_keys)
            plaintext, prefix = svc.mint_key(args.email, args.tier)
            print(f"minted key for {args.email} (tier={args.tier})")
            print(f"  prefix : {prefix}")
            print(f"  KEY    : {plaintext}")
            print("  ^ shown once — store it now (only the hash is saved).")

        elif args.cmd == "set-tier":
            svc = AdminService(provider.users, provider.api_keys)
            n = svc.set_tier(args.prefix, args.tier)
            print(f"updated {n} key(s) to tier={args.tier}")

        elif args.cmd == "list":
            svc = AdminService(provider.users, provider.api_keys)
            rows = svc.list_keys()
            if not rows:
                print("(no keys)")
            for r in rows:
                print(f"  {r['key_prefix']:12}  {r['tier']:7}  {r['email']}")

        elif args.cmd == "resolve":
            svc = EntitlementService(provider.api_keys, provider.devices)
            print(svc.resolve(security.hash_key(args.key), args.device))
    finally:
        provider.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
