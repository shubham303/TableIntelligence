"""Connector base + registry.

A connector's ONLY jobs: authenticate with a credential it is *given* (never one it
stores), pull data directly from the provider to this machine, and normalize it into
the canonical contract (`contract.conform`). Credential handling stays out of connector
logic so real OAuth later is config, not a rewrite. Data never routes through our server.
"""
from __future__ import annotations

import abc

import pandas as pd


class Connector(abc.ABC):
    #: short id, e.g. "stripe"
    name: str = ""
    #: canonical entities this connector can produce
    entities: tuple[str, ...] = ()
    #: plain-language guidance for the agent on how to analyze this source
    platform_prompt: str = ""

    @abc.abstractmethod
    def fetch(self, credential: str, *, limit: int = 1000, **opts) -> dict[str, pd.DataFrame]:
        """Pull + normalize. Returns {entity_name: canonical DataFrame}. The
        credential is passed in (env/config), never held by the connector."""

    def materialize(self, tables: dict[str, pd.DataFrame], dest_dir: str) -> dict[str, str]:
        """Write canonical tables to CSVs under ``dest_dir`` so they can be loaded
        into a session. Returns {entity_name: csv_path}."""
        import os

        os.makedirs(dest_dir, exist_ok=True)
        paths: dict[str, str] = {}
        for name, df in tables.items():
            path = os.path.join(dest_dir, f"{name}.csv")
            df.to_csv(path, index=False)
            paths[name] = path
        return paths


_REGISTRY: dict[str, type[Connector]] = {}


def register(cls: type[Connector]) -> type[Connector]:
    _REGISTRY[cls.name] = cls
    return cls


def get_connector(name: str) -> Connector:
    if name not in _REGISTRY:
        raise ValueError(f"Unknown connector {name!r}; available: {list_connectors()}")
    return _REGISTRY[name]()


def list_connectors() -> list[str]:
    return sorted(_REGISTRY)
