"""Social-content agent feature — templates → campaigns → search targets +
drafted posts, plus feedback. Mirrors the outreach agent's shape: a thin
data/CRUD surface over the user's Table Intelligence account via the
integration control-plane client.

ONE COMPONENT, not the whole system. Governing principle — **own the read,
defer the write** (see ``AGENTS.md``), applied here as:

* **Reads we DEFER to the harness** — discovering recent reddit threads,
  Medium articles, tweets, etc. is a read, but those sources are too varied
  and too vendor-specific (each platform's API/scraper the user picks) for us
  to own. Instead the agent emits structured SEARCH SPECS (platform, queries,
  scopes, recency, keywords) saved to the dashboard; the HARNESS runs them
  with whatever web-search / reddit / scraper tools the user has installed
  and hands the results back. This keeps the agent vendor-neutral and avoids
  baking brittle per-platform scrape code into a deterministic engine.
* **Writes we DEFER to the harness** — posting a LinkedIn update, publishing a
  Medium article, sending a tweet, replying on a reddit thread, posting in a
  Facebook group. These mutate external systems the user owns and picks the
  vendor for. The agent drafts the content + (for replies) saves the target
  URL + the exact reply text; the user copies/pastes or the harness's own
  browser/social tools post it. Mirrors outreach's "we don't send email".
* **Other agents are independent** — no code coupling to ``tabint.outreach``,
  ``tabint.analysis``, or ``tabint.seo_agent``; the harness composes them at
  runtime. See ``AGENTS.md``.

Honesty boundary: the agent drafts content and emits search specs; it NEVER
publishes, posts, replies, or automates engagement on any platform directly.
The harness/user executes each outward action with explicit approval.
"""
