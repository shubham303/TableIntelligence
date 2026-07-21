# Using TableIntelligence from an AI agent

The deterministic core is exposed through two surfaces, both driven by a **session
key** that identifies a session and its data across calls:

- **MCP server** (`tabint-mcp`) — for MCP clients (Claude Cowork / Claude Code /
  Claude Desktop, OpenAI Codex, Cursor).
- **CLI** (`tabint`) — for terminal agents (Claude Code bash), JSON in/out.

Both persist state on disk under `<TABULAR_BASE>/.tableint/sessions/<session_key>/`,
so an agent can `load` once and then chain `train → evaluate → add_predictions`
across separate calls or a server restart.

## Install

The package is **private** (not on PyPI — it carries the
`Private :: Do Not Upload` classifier), so install from source. Requires
Python ≥ 3.10.

```bash
git clone https://github.com/shubham303/TableIntelligence.git
cd TableIntelligence
pip install -e ".[mcp]"     # library + `tabint` CLI + `tabint-mcp` server
```

This installs four console scripts (two branded aliases):

| Script | Runs | Source |
| --- | --- | --- |
| `tabint` | the CLI | `tabint.cli:main` |
| `tabint-mcp` | the MCP server | `tabint.mcp_server:main` |
| `table-intelligence` | the CLI (alias) | `tabint.cli:main` |
| `table-intelligence-mcp` | the MCP server (alias) | `tabint.mcp_server:main` |

Sanity-check before registering with an agent:

```bash
tabint --help
tabint-mcp --help
```

## Environment variables

Set these in the MCP server's `env` (or your shell for the CLI).

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `TABINT_API_KEY` | **yes** | — | Your key, from `https://shubhamrandive.com/dashboard/account`. Absent → free tier: all analytics still work, but paid connectors / cloud reports / outreach are gated. |
| `TABINT_CONTROL_PLANE_URL` | no | `https://shubhamrandive.com` | Base URL of the control plane (report/folder storage, key validation). |
| `TABULAR_BASE` | no | current dir | Where on-disk sessions live (`<base>/.tableint/sessions/<key>/`). |

## Register the MCP server

`tabint-mcp` speaks the **stdio** transport. Pick the block for your agent.

### Claude Code / Claude Cowork / Claude Desktop

Register via the Claude Code CLI:

```bash
claude mcp add tabint \
  --env TABINT_API_KEY=sk_your_key_here \
  --env TABINT_CONTROL_PLANE_URL=https://shubhamrandive.com \
  -- tabint-mcp
```

…or paste this into the MCP config JSON (Cowork / Desktop):

```json
{
  "mcpServers": {
    "tabint": {
      "command": "tabint-mcp",
      "env": {
        "TABINT_API_KEY": "sk_your_key_here",
        "TABINT_CONTROL_PLANE_URL": "https://shubhamrandive.com"
      }
    }
  }
}
```

### OpenAI Codex (CLI)

Codex reads MCP servers from `[mcp_servers.*]` in `~/.codex/config.toml`
(`CODEX_HOME` overrides that directory):

```toml
[mcp_servers.tabint]
command = "tabint-mcp"
args = []
env = { TABINT_API_KEY = "sk_your_key_here", TABINT_CONTROL_PLANE_URL = "https://shubhamrandive.com" }
```

### Cursor

Drop this at `.cursor/mcp.json` in your project (or *Settings → MCP* for a
global install):

```json
{
  "mcpServers": {
    "tabint": {
      "command": "tabint-mcp",
      "env": {
        "TABINT_API_KEY": "sk_your_key_here",
        "TABINT_CONTROL_PLANE_URL": "https://shubhamrandive.com"
      }
    }
  }
}
```

## Verify it works

After registering, ask the agent to call the `account_status` tool. With a valid
key it returns your tier; with no key it reports `free` (analytics still work):

```text
> call account_status
{"tier": "paid", "entitled": true, ...}
```

To pin a session-store location, set `TABULAR_BASE` too — e.g.
`"TABULAR_BASE": "/Users/me/tabint-work"` in the `env` block.

## Tool workflow

1. `create_session(paths)` → returns `session_key`, `tables`, and detected
   foreign-key `relationships`.
2. Pass `session_key` to every later tool. Analytics act on ONE `table` — an
   uploaded table or one made by `join(session_key, tables)`.
3. Each tool returns `{method, summary, values, metadata}` — the method was chosen
   deterministically, so the agent doesn't pick the statistical test itself.

Representative tools: `create_session`, `session_info`, `list_sessions`,
`add_table`, `relationships`, `join`, `run_sql`, `profile`, `detect_outliers`,
`analyze_association`, `association_matrix`, `cluster`, `profile_clusters`,
`reduce_dimensions`, `train_classifier`, `train_regressor`, `evaluate`,
`feature_importance`, `add_predictions`, `explain_prediction`, `decompose`,
`forecast`, `account_status` (full list exposed by the server; call
`list_sessions` / ask the agent to enumerate tools).

## CLI

Every command prints a JSON object; `--session <key>` threads state between calls.

```bash
tabint load orders.csv customers.csv products.csv        # -> {"session_key":"s_ab12", ...}
tabint relationships --session s_ab12
tabint join orders customers --session s_ab12 --name enriched
tabint associate order_total tier --session s_ab12 --table enriched
tabint train-classifier is_churned --session s_ab12 --table customers --name churn
tabint evaluate --session s_ab12 --table customers --model churn
tabint sql "SELECT tier, COUNT(*) n FROM customers GROUP BY tier" --session s_ab12
```

Run `tabint --help` (or `tabint <command> --help`) for the full verb list.

## Notes

- Trained models are pickled into the session; unpickling requires the same
  scikit-learn version used to train (pin it in production).
- The CLI opens the on-disk session each call; the MCP server keeps sessions live
  in memory and falls back to disk on a cache miss, so a key survives restarts.
- `tabint-mcp` and `table-intelligence-mcp` are the same entry point under two
  names — use whichever your config style prefers.
