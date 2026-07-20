# Steps for Shubham — accounts & deploys to set up later

Things **only you can do** (account creation, secrets, deploys). Everything else is built to run
locally with no accounts. Check off as you go.

## Architecture recap (so the steps make sense)
- **MCP server (Python, local)** — analytics only. Uses DuckDB *just to load CSVs for analysis*.
  No user data. Calls the website's APIs for entitlement + report save/list.
- **Website (shubham-site, Astro + Vercel, TypeScript)** — the whole control plane: users, auth,
  subscriptions (**Razorpay**), reports/folders, dashboard, docs, and the APIs the MCP calls.
  DB facade: **DuckDB when run locally, Neon/Postgres in production** (chosen by env).

> **Local dev needs no accounts:** run the website locally and it uses a local DuckDB file; the
> MCP points at your local website URL. Razorpay/Neon are only for production.

---

## 1. Razorpay (payments)
- [ ] Create a Razorpay account.
- [ ] Create a **Subscription Plan** for premium (₹/$ amount — ~US$5/mo equivalent) with a
  **3-day free trial** before the first charge.
- [ ] Get **test-mode** `key_id` + `key_secret`, and add a **webhook** (subscription + payment
  events) with its signing secret.
- [ ] Give me the plan ID + test keys → I'll wire Razorpay checkout + webhook in the website
  (updates the user's subscription + tier).

## 2. Neon (production database)
- [ ] Create a Neon project (neon.tech or via Vercel Marketplace).
- [ ] Set the pooled connection string as `DATABASE_URL` in the **website's** Vercel env vars.
  - The website's DB facade auto-switches to Postgres when `DATABASE_URL` is set; DuckDB otherwise.

## 3. Vercel (deploy the website)
- [ ] Deploy shubham-site to Vercel with SSR (adapter already configured).
- [ ] Set env vars: `DATABASE_URL` (Neon), `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`,
  `RAZORPAY_WEBHOOK_SECRET`, `SESSION_SECRET`.
- [ ] The MCP client points `TABINT_CONTROL_PLANE_URL` at the deployed site (e.g.
  `https://shubhamrandive.com`).

## 4. Publishing the MCP server (distribution)
- [ ] Reserve the PyPI name (`table-intelligence`) → I flip the `Private :: Do Not Upload`
  classifier and publish.
- [ ] (Later) Build + sign the `.mcpb` one-click bundle for the Claude Desktop directory.

---

## Superseded (for reference)
The Python `control-plane/tabint_control/` package (DuckDB/Postgres repos + services) was the
first cut of the control plane. Per the pivot, the control plane now lives **in the website
(TypeScript)**; that Python package is the **schema/logic blueprint** for the TS port, not the
deployed backend. The Stripe *data connector* is unrelated to payments and still valid.

**When any account is ready, tell me and I'll wire the code side.** Nothing here blocks the local
build.
