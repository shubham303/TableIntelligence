"""Connectors — pull data from a source and normalize it to the canonical contract.

Single MCP server, many connectors: each registers itself and emits the shapes in
`contract.py`. The MCP server is free to use with no client-side gating; data is
fetched provider→machine directly (it never transits the control plane).
"""
from . import contract
from .base import Connector, get_connector, list_connectors, register
from . import stripe  # noqa: F401 - registers StripeConnector

__all__ = ["Connector", "contract", "get_connector", "list_connectors", "register"]
