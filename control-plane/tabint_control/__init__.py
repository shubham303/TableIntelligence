"""Table Intelligence control plane — layered (repository → service → endpoint).

Strict layering:
  * ``repositories`` — one class per table, table access only (no logic).
  * ``services``     — business logic; depends only on repositories.
  * ``db``           — the `Database` facade + factory that hides the engine.
  * endpoints        — the CLI (``cli.py``), the client's local-mode call, and
                       (prod) a web handler — each depends only on services.

Backend is chosen from the environment by the factory, so services are
DB-agnostic: DuckDB for local dev, Postgres/Neon in production.
"""
from .db import create_provider
from .services import AdminService, EntitlementService
from . import security

__all__ = ["create_provider", "AdminService", "EntitlementService", "security"]
