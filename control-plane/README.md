# Table Intelligence — Control Plane

Thin backend: auth keys, 2-device cap, subscriptions/trials. **No raw user data ever lives here.**
Runs on **DuckDB locally** (a file, zero setup) and **Postgres/Neon in production** — the same
code, the backend is chosen from the environment.

## Architecture — strict layering (repository → service → endpoint)
```
tabint_control/
  db/
    database.py     Database facade (DuckDBDatabase | PostgresDatabase) — the ONLY code that
                    knows a driver. ? placeholders everywhere; rewritten to %s for Postgres.
    factory.py      create_provider() reads the env, builds the right Database, wraps it in a
                    RepositoryProvider facade. Hides the DB from everything above.
  repositories/     ONE class per table, table access only, no business logic:
    users.py  api_keys.py  devices.py  subscriptions.py
  services/         Business logic; depends only on repositories:
    entitlement_service.py   resolve(key_hash, device_id) + 2-device cap
    admin_service.py         mint_key / set_tier / list_keys
  cli.py            An ENDPOINT (depends only on services). Local/dev admin.
  security.py       key generation + hashing (only hashes are stored)
```
- **Repositories never call each other or hold logic.** Cross-table composition (e.g. key + owner
  email) happens in a **service**, not a repository join.
- **Services never see a `Database` or a connection string** — only repositories from the factory.
- **Endpoints** = this CLI (dev/admin) and, in production, **shubham-site's web endpoints**
  (validate-key, Stripe webhook, account/metadata) which reuse these same services.

## Backend selection (factory, first match wins)
- `DATABASE_URL=postgres://…`  → Postgres/Neon (production)
- `TABINT_CONTROL_DB=/path.duckdb` → DuckDB at that path (local dev)
- otherwise → DuckDB at `~/.tabint/control.duckdb`

## Local development — no accounts needed
```bash
uv pip install -e ./control-plane            # once
export TABINT_CONTROL_DB=~/.tabint/control.duckdb
python -m tabint_control.cli init            # create tables
python -m tabint_control.cli mint --email you@example.com --tier paid
python -m tabint_control.cli list
python -m tabint_control.cli resolve --key ti_xxx --device dev-1   # test the flow
```
The MCP server's `entitlement.py` uses these same services in local mode (set `TABINT_CONTROL_DB`
+ `TABINT_API_KEY`); in production it calls the `validate-key` web endpoint over HTTP.

## Production
See `../steps_for_shubham.md` (Neon + Stripe + shubham-site deploy). The Postgres backend is the
same code path — set `DATABASE_URL` and run `init` (or apply via shubham-site) to create the schema.

## Tests
`../tests/test_control_plane.py` (repositories/services on DuckDB) and
`../tests/test_entitlement.py` (client local-mode). Run: `python -m pytest tests/ -q`.
