"""Integration — all external API clients, split into schemas (canonical shapes)
and service (client implementations).

The connector surface (``list_connectors`` / ``get_connector``) is re-exported here
so callers can do ``from tabint.integration import list_connectors``; importing
this package also registers the built-in Stripe connector.
"""
from tabint.integration.service.base import Connector, get_connector, list_connectors, register
from tabint.integration.service import stripe  # noqa: F401 - registers StripeConnector

__all__ = ["Connector", "get_connector", "list_connectors", "register"]
