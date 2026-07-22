"""Connectors — pull data from a source and normalize it to the canonical contract.

Single MCP server, many connectors: each registers itself and emits the shapes in
`contract.py`. Connectors are a Pro feature; the MCP tools that invoke them are gated
with `entitlement.requires_pro`. Data is fetched provider→machine directly.
"""
from . import contract
from .base import Connector, get_connector, list_connectors, register
from . import stripe  # noqa: F401 - registers StripeConnector

__all__ = ["Connector", "contract", "get_connector", "list_connectors", "register"]
