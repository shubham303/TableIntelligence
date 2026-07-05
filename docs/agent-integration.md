# Using TableIntelligence from an AI agent

The deterministic core is exposed through two surfaces, both driven by a **session
key** that identifies a session and its data across calls:

- **MCP server** — for MCP clients (Claude Cowork, Claude Desktop, Claude Code).
- **CLI** (`tabular`) — for terminal agents (Claude Code bash), JSON in/out.

Both persist state on disk under `<base>/.tableint/sessions/<session_key>/`, so an
agent can `load` once and then chain `train → evaluate → add_predictions` across
separate calls or a server restart.

## Install

```bash
pip install -e ".[mcp]"     # library + CLI + MCP server
```

This installs two console scripts: `tabular` (CLI) and `tabular-mcp` (MCP server).

## MCP server

Run manually (stdio transport):

```bash
TABULAR_BASE=/path/to/workdir tabular-mcp
```

`TABULAR_BASE` sets where sessions are stored (default: current directory).

### Add to Claude Code

```bash
claude mcp add tabular -- tabular-mcp
# or, to pin the session store location:
claude mcp add tabular --env TABULAR_BASE=/path/to/workdir -- tabular-mcp
```

### Add to Claude Cowork / Claude Desktop

Add to the MCP config JSON:

```json
{
  "mcpServers": {
    "tabular": {
      "command": "tabular-mcp",
      "env": { "TABULAR_BASE": "/path/to/workdir" }
    }
  }
}
```

### Tool workflow

1. `create_session(paths)` → returns `session_key`, `tables`, and detected
   foreign-key `relationships`.
2. Pass `session_key` to every later tool. Analytics act on ONE `table` — an
   uploaded table or one made by `join(session_key, tables)`.
3. Each tool returns `{method, summary, values, metadata}` — the method was chosen
   deterministically, so the agent doesn't pick the statistical test itself.

Tools: `create_session`, `session_info`, `list_sessions`, `add_table`,
`relationships`, `join`, `run_sql`, `profile`, `detect_outliers`,
`analyze_association`, `association_matrix`, `cluster`, `profile_clusters`,
`reduce_dimensions`, `train_classifier`, `train_regressor`, `evaluate`,
`feature_importance`, `add_predictions`, `explain_prediction`, `decompose`,
`forecast`.

## CLI

Every command prints a JSON object; `--session <key>` threads state between calls.

```bash
tabular load orders.csv customers.csv products.csv        # -> {"session_key":"s_ab12", ...}
tabular relationships --session s_ab12
tabular join orders customers --session s_ab12 --name enriched
tabular associate order_total tier --session s_ab12 --table enriched
tabular train-classifier is_churned --session s_ab12 --table customers --name churn
tabular evaluate --session s_ab12 --table customers --model churn
tabular sql "SELECT tier, COUNT(*) n FROM customers GROUP BY tier" --session s_ab12
```

Run `tabular --help` (or `tabular <command> --help`) for the full verb list.

## Notes

- Trained models are pickled into the session; unpickling requires the same
  scikit-learn version used to train (pin it in production).
- The CLI opens the on-disk session each call; the MCP server keeps sessions live
  in memory and falls back to disk on a cache miss, so a key survives restarts.
