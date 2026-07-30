"""MCP server entry point — the composition root.

This module is intentionally thin: it does nothing but import the analysis
``tools`` module so its ``@mcp.tool()`` definitions register onto the single
FastMCP instance held in ``tabint.shared.server``, then expose ``main()`` to run
it over stdio. All tool logic lives in ``analysis/tools.py``.

Run with:  ``python -m tabint.app.mcp_server``  or the ``tabint-mcp`` console
script. Set ``TABULAR_BASE`` to control where sessions are stored (default: cwd).
"""
# Importing this module registers its @mcp.tool() / @mcp.prompt() decorators on
# the shared FastMCP instance.
from tabint.analysis import tools as _analysis_tools  # noqa: F401

from tabint.shared.server import mcp


def main() -> None:
    """Entry point: run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
