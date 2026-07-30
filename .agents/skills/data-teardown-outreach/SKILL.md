---
name: data-teardown-outreach
description: >
  Find and win data-analysis clients for a solo consultant. Use this whenever the
  user wants to prospect for clients, find businesses to email, build a target list,
  run a "teardown" or free-sample analysis on a company's public data, or draft a
  cold email — a simple, capability-led pitch ("I'm a data scientist; if you're
  struggling with a lot of data, I can help"), with the teardown used for internal
  qualification, not embedded in the email. Cold email is the only outreach channel
  (social platforms are for knowledge-sharing, not ads). Trigger
  on phrases like "find me some clients", "who should I email", "run a teardown on
  X", "draft a cold email to X", "build my prospect list",
  or any request to generate outreach for the data-analysis service. Covers any
  vertical that can pay and has data worth analysing — e-commerce is the biggest, but
  also SaaS, marketing agencies, nonprofits, and any data-rich, analyst-poor business —
  across the whole English-speaking world (Dubai, Europe, US, Canada, UK, Singapore,
  Australia, New Zealand, India), not just the US. This is a marketing/sales workflow, not
  the deep paid analysis itself.
---

# Data Teardown & Outreach

This skill runs the client-acquisition loop for a **solo data-analysis service**: find
the right businesses, run a "teardown" on their *public* data to qualify them, and draft a
**simple, capability-led cold email** — say who you are (a data scientist), name where you
can help across **both services** (data insights extraction **and** AI-agent automation),
leave the door open to any data problem, and point to a credibility website. The
teardown is for *internal qualification*, **not** embedded in the email — keep the message
plain and human. The operator (Shubham) reviews every draft and sends every message by hand
— this skill produces **drafts and analysis**, never auto-sends.

## The business this serves (context)

The operator sells **two related services**:

1. **Data insights extraction** — takes a client's messy data (sales, orders, marketing,
   donations, etc.) and produces reports with genuine, revenue-driving insights.
2. **AI agent automation** — builds AI agents to automate a client's repetitive or
   manual tasks (data pulls, report generation, workflows, anything an agent can take
   off their plate). Whenever the data pitch lands, offer this as a natural second thing
   he can help with; some prospects need the automation more than the analysis.

The go-to-market is **service-first**: land clients by doing a free sample
analysis, charge per report or on retainer, and productize later. He has a low cost
base (based in India), so clients paying a price that feels *cheap to them* is strong
income for him — but sell **specialization, not cheapness**.

**Target market (broad — do not narrow prematurely):**
- **Any vertical**, not just ecommerce. The only qualifier: the prospect **can pay** and
  **has data they want analysed**. Ecommerce, SaaS, marketing agencies, nonprofits,
  finance, healthcare, logistics — all fair game if they meet that bar.
- **The whole English-speaking world**, not just the US: Dubai/UAE, Europe, USA, Canada,
  UK, Singapore, Australia, New Zealand, and India. Don't build US-only prospect lists.

The whole business right now is a **distribution problem**, not a tech problem. The
analysis engine already exists. So this skill's job is to make prospecting and outreach
fast and high-quality — not to rebuild analysis tooling.

## What this skill does, end to end

1. **Find & qualify prospects** — build a list of businesses that fit the target profile.
2. **Run a teardown (for qualification, not for the email)** — pull the prospect's *public*
   data to confirm they fit and to brief the operator. **Do not put the finding in the cold
   email** — findings are for internal qualification and for the *reply*, not the first touch.
3. **Draft outreach** — a **capability-led cold email**: state who you are (data scientist),
   name where you can help (data wrangling, analysis, reports, insights), leave the door open
   to any data problem, and point to the credibility website in the signature. No diagnosis of
   their business, no pricing in the body — the ask is just "if it sounds like something you could use, happy to talk".
4. **Hand off for review & send** — present drafts for the operator to sharpen and send.

Do these in order when asked for the full loop, or jump to whichever step the operator
asks for.

---

## Step 1 — Find & qualify prospects

**Who we're looking for (the universal pattern).** A good prospect has all five:

1. **Has data but no one to analyze it** — real data piling up, no in-house analyst/BI.
2. **Can and will pay** — a real business or funded org with budget; ideally already
   buys software/tools.
3. **The decision-maker reads their own inbox** — owner-operated or small team, not a
   faceless corp with gatekeepers.
4. **Recurring reporting need** — the same analysis repeats monthly/quarterly, so a
   one-off report can become a retainer.
5. **Has public data for a teardown hook** — something you can analyze *before* contact
   to prove value.

**Who to skip (anti-targets):**

- **Whales** — big enough to already have a data team or agency; they ignore cold email.
- **Hobbyists / micro-operators** — no budget at any price (e.g., a shop earning a few
  hundred dollars a year).
- **Broke or grant-only nonprofits** — spending on "overhead" is a board/donor problem
  for them, so budget rarely exists.
- **No-data or purely offline businesses** — nothing to analyze.
- **Sensitive-data-only targets early on** (health PII, etc.) — revisit once established.

**Tier every prospect (this drives the offer + price).** After qualifying, tag each one
by rough annual revenue — the fee only works when it's a small slice of the value you can
move, and that ratio depends on their size:

| Tier | Client revenue | Offer shape | Price | Delivery |
|------|----------------|-------------|-------|----------|
| **retainer-tier** | ~$1M+/yr | sample → paid report → **monthly retainer** | $500–2,500/mo | can be higher-touch |
| **report-tier** | ~$100k–$500k/yr | sample → **one-off paid report** (retainer only if *they* ask) | $200–500/report | must be fast + **templated** |
| *(skip)* | < ~$100k/yr | — | — | ROI math is impossible; anti-target |

Two rules that come with the tiers:
- **report-tier is a velocity game, not a high-touch one.** A $300 report is only
  profitable if it takes hours, not a full day — lean on the deterministic engine and
  templates. If a small client needs 8 custom hours, the tier doesn't work.
- **Scope the insight to their data volume.** A ~$100k/yr shop may have only hundreds of
  orders; cohort retention / forecasting / elasticity need volume to be trustworthy. For
  report-tier, lead with methods that work on small n (RFM, repeat-rate, AOV/margin) and
  don't over-promise the heavy modeling.

Tag the tier in the tracker and let it pick the offer (see Step 3).

Don't fixate on one vertical or one country. **Any vertical qualifies as long as the
prospect can pay and has data they want analysed** — ecommerce, SaaS, marketing agencies,
nonprofits, finance, healthcare, logistics, and more. E-commerce is the largest and
easiest slice, but marketing agencies convert best on money and nonprofits have the
richest public data. And target the **whole English-speaking world**, not just the US:
Dubai/UAE, Europe, USA, Canada, UK, Singapore, Australia, New Zealand, and India are all in
scope. **For the full, detailed breakdown of each vertical — who they are, what they do,
their pain, the public-data hook, and how much money is realistically there — read
[`references/client-profiles.md`](references/client-profiles.md).** Consult it whenever
building a target list or deciding whether a prospect is worth the effort.

**Qualify before spending time.** For each candidate, check the five signals above. If
fewer than three are clearly true, skip it — a badly-targeted list turns effort into
zero replies. Prefer **tight sub-niches** (e.g., "Shopify skincare brands doing
$50k–500k/mo") over broad categories, because a niche makes the teardown speak the
prospect's language and word of mouth travels fast inside it.

**Find real recipient names — and don't stop at the founder.** Target **several
decision-makers** at each prospect, not just one. Good roles: founder/CEO, but also the
COO, head/VP of marketing or growth, head of ecommerce/operations, head of data/analytics,
or whoever most owns the metric your finding speaks to (a growth finding → the growth
lead; an ops finding → the COO). For each, get a **named human + their title**, then run
the email-discovery protocol below to find their actual address.

### Email discovery — do this per prospect, in order (don't stop at guessing)

Finding the *correct* address is worth real effort: a wrong guess bounces, wastes the
send, and (in volume) hurts domain reputation. **Guessing from a pattern is the last
resort, not the first move.** For every prospect, work these sources in order and stop as
soon as you have a *published, verifiable* address for a named human:

1. **The company website — read it properly, not just the homepage.** Fetch and actually
   read: Contact, About, Team, Leadership, Meet-the-team, Careers, Press/Media, and the
   **page footer** and **privacy policy / terms / imprint** (EU/UK sites are legally
   required to publish a contact email in the imprint/legal notice). Many sites hide real
   addresses in the footer or a "media enquiries" line rather than a contact form.
2. **Targeted web search.** Run several queries, don't settle for one:
   `"<Company>" contact email`, `"<Person name>" "<company.com>" email`,
   `site:<company.com> email`, `"<Person>" <company> linkedin`, and
   `"@<company.com>"` to surface the domain's real address format in the wild.
3. **LinkedIn & socials.** Confirm the person still works there and owns the area; some
   profiles or company "About"/contact sections list a direct or generic email.
4. **Directory / data sources.** RocketReach, Hunter.io, Clearbit-style pages, Apollo,
   ZoomInfo snippets, Crunchbase — these often surface the *verified pattern* and
   sometimes the exact address, with a confidence score. Treat their guesses as
   hypotheses, not facts.
5. **Pattern inference — only as a fallback, and only if the format is actually observed.**
   If (and only if) you have seen the domain's real format somewhere (e.g. a published
   `jane.doe@acme.com`), infer a named person's likely address from that same pattern.
   Never invent a format you haven't seen.

**Verify before you send.** Run every candidate address through a free deliverability
check (Hunter/NeverBounce/ZeroBounce free verifier, or an MX + SMTP catch-all check).
Discard anything that fails or is a catch-all you can't confirm.

**Record the source and confidence for each address** in the tracker: mark it
`published` (found live on the site/a directory — highest trust), `verified` (passed a
deliverability checker), or `inferred` (pattern-guessed — lowest trust, send last or not
at all). **Prefer a published, named human over a guessed one, and both over `info@`.**
If the only thing you can find is a generic `info@`/`hello@`, use it — a delivered generic
beats a bounced guess.

- Log **2–4 contacts per prospect** in the tracker so a single non-reply doesn't kill the
  lead — you can reach a second decision-maker. Don't blast the same email to all of them
  at once; space them, and tailor the finding to each person's area.
- **Never send to an `inferred` address as the only recipient.** Pair it with a
  `published`/`verified` address, or verify it first — this is exactly the failure that
  causes bounces.

---

## Step 2 — Run the teardown (public data only)

The teardown is a short analysis of the prospect's **public** data, used purely to earn
the conversation. It is *not* the paid analysis (that needs their private data).

**Pick the data source by vertical:**

- **Shopify store** → pull the catalog from `https://<domain>/products.json`
  (paginate `?limit=250&page=N`). Use `scripts/shopify_teardown.py` — it computes the
  findings deterministically. Reviews add complaint/loved-product themes.
- **Etsy shop** → no `products.json`; the shop page blocks naive scraping. Use the
  **Etsy Open API v3** (`getListingsByShop`) with a registered key, a research tool
  (eRank / EtsyHunt / Everbee / Alura) for listing counts, prices, and estimated sales,
  and the **public reviews page** for review-theme mining. The Etsy teardown is a
  *review-and-reputation* teardown more than a catalog one.
- **US nonprofit** → pull the **IRS Form 990** from ProPublica's Nonprofit Explorer or
  Candid. Multi-year revenue, expenses, program-expense ratio, fundraising efficiency,
  and exec comp are all public — a strong hook needing zero trust.
- **Other businesses** → use whatever is public: website, pricing pages, catalog,
  reviews, app-store listings, public filings, Similarweb-style traffic estimates.

**What makes a finding good:** specific, tied to something that matters (usually money),
and *honest* — including at least one genuine positive so it reads as analysis, not a
pitch. Because it's built on public data, every finding is a **hypothesis** ("this might
be costing you X"), never a stated fact about their sales. Over-claiming on public data
is the fastest way to lose credibility.

**Standard teardown output:** 2 real findings + 1 positive + a one-line note on what the
public data *can't* show (revenue, margin, repeat buyers) that teed up the paid analysis.

---

## Step 3 — Draft outreach

Draft the message; the operator sharpens and sends it. **Cold email is the only outreach
channel.** Social platforms (LinkedIn, Reddit, Medium, Twitter) are for *knowledge-sharing
to build credibility*, not advertising — this skill does not draft promo posts for them.
That credibility content (the website blog + syndicated posts) has its own playbook and
guardrails in [`references/content_creation_guide.md`](references/content_creation_guide.md)
— **consult it before drafting or publishing any blog/social content.** Key rule: never
publish the named teardown you sent a prospect; publish only open-dataset or anonymized
findings.

### Cold email

**Capability-led, warm, phone-readable, and adapted to the company.** The motion is
**observation → time-framed offer → concrete capability → website-as-proof → question close**.
A credibility website (mid-body) does the real convincing. **Do NOT diagnose their business or
embed a teardown finding** — earlier "clever" drafts that critiqued the prospect's setup were
too complicated, presumptuous, and often wrong. Keep it simple; they may have a different data
problem than you'd guess.

**Adapt every email to the specific company — it is not a fixed form-letter.** The skeleton is
constant, but three things are rewritten per prospect from what you learned qualifying them:
- **The observation** — their actual channels/model ("an independent roastery selling direct",
  "SEO and Google Ads for a roster of clients", "an Ayurvedic skincare brand with a broad range").
- **The data you name** — match their vertical: ecommerce → *sales and customer data*; a
  nonprofit → *donation and program data*; a SaaS → *usage and subscription data*; an agency →
  *campaign and client data*. Never say the generic "your data" when you can name theirs.
- **The subject and the payoff** — the benefit that matters to *this* business (growth,
  retention, fundraising efficiency, etc.).

Structure:
1. **Observation + time-framed offer (this goes FIRST).** Open with **one light observation**
   you could only know by looking at their site — kept light, not too specific
   (e.g. "You run an independent roastery selling direct—which means your business generates a
   lot of data"). It's an *observation, never a diagnosis*. Then frame the pain around **their
   time**: "If pulling that information together and finding clear, actionable insights from it
   takes up too much of your time, I can help." One clean pain, not a laundry list.
2. **Who you are + concrete, outcome-led capability.** "I'm a data scientist, and I build AI
   tools that look at [their data, e.g. sales and customer data] to highlight the trends that
   actually matter for your growth." Name *their* data and the *payoff*, not abstract "insights".
   Then name the **second service in one line**: "I also build AI agents that automate the
   manual, repetitive work that eats your time." Two services, both stated — data insights
   **and** AI-agent automation. Keep it to one line so the email stays tight.
3. **Website as proof (in-body).** "My website (shubhamrandive.com) showcases how I do this."
4. **Question close.** "Open to a quick chat about how to get more value out of your [store's/
   business's] data?" — a question invites a reply better than "happy to talk".
5. **Warm sign-off.** "Best, Shubham." The only link anywhere is `shubhamrandive.com` (no
   LinkedIn, Calendly, Medium, Twitter, email URLs) — every other profile is reachable from it.

**Do NOT** put pricing or the sample-then-paid model in the body. The teardown/tier is internal
qualification only — don't reference it in the cold email; save specifics for the reply. Use a
**benefit subject** (e.g. "Making sense of your store's data"), and **vary it across a batch**
so identical subjects don't read as mass-mail.

See `references/outreach-templates.md` for the ready template and the reusable principles.

---

## Step 4 — Hand off for review & send

**Persist every teardown to disk** so the batch is reviewable and reusable. Write one
Markdown file per client under a date-stamped folder at the project root:

```
.Codex-artifacts/teardown-outreach/<YYYY-MM-DD>/<client-slug>.md
```

- `<YYYY-MM-DD>` is today's date (the sourcing/teardown run date); create the folder if
  it doesn't exist. `<client-slug>` is the brand name lowercased and hyphenated
  (e.g. `cocokind.md`, `peace-out-skincare.md`).
- Each file holds, for that one client: the qualification summary (domain, the **2–4
  named decision-makers with roles + emails** — founder/CEO plus other top-level people
  like COO, head of marketing/growth, head of ecommerce/data — and the five-signal
  check), the **raw deterministic teardown numbers** from the
  script, the phrased findings (2 real + 1 positive + the "what public data can't show"
  line), and the drafted outreach (subject + body). Keep the raw script output in the
  file so a finding can always be traced back to a number.
- Also maintain an `index.md` in the date folder: a one-line-per-client status row
  (client · **tier** (retainer / report) · **contacts** (named people + roles reached) ·
  sharpest finding · status: drafted / sent / replied / sample-shared / paid) — this is the
  tracker referenced below. Track status per-contact when you reach more than one person.
- Never write customer PII into these files; they hold public-catalog findings and drafts
  only.

Present the teardown findings and the draft message together. Remind the operator to:
- **Review and sharpen the finding** with domain knowledge before sending — the human
  review is the quality gate and is never skipped.
- **Have the paid deliverable ready** so a "yes" can be answered within the hour.
- **Send by hand** (keeps volume sane, deliverability high, and forces the review).
- **Log** the send in the tracker (sends → replies → samples shared → paid) and
  **follow up once** at ~4–5 days if no reply.

---

## Guardrails (non-negotiable)

These protect credibility — a single wrong claim in a cold email kills the lead.

- **Numbers come from code, not the model.** All teardown figures (price bands, counts,
  ratios, financial deltas) must be computed by deterministic scripts. The LLM only
  *phrases* findings; it never eyeballs data and states numbers, because it will
  occasionally be confidently wrong. This mirrors the product's own architecture:
  deterministic math, generated prose.
- **Public-data findings are hypotheses.** Frame them as "worth checking against your
  numbers," never as proven facts about their business.
- **Never auto-send.** This skill outputs drafts. The operator reviews and sends every
  message and post by hand.
- **Include a positive.** An all-criticism teardown reads as manufactured.
- **Respect scraping etiquette.** Add delays between requests, don't hammer endpoints,
  and skip any source that blocks automated access rather than fighting it.
- **Strip/avoid personal data.** Never collect customer PII in a teardown; tell prospects
  to strip it from any export they later share.

## Daily rhythm (when asked to plan the work)

Two focused hours/day, weighted to sending, not tooling:
- ~30 min source & qualify 10 prospects (with real names).
- ~60 min run teardowns + draft and **send** 10 emails (the send count is the
  non-negotiable — the day isn't done until they're sent).
- ~30 min knowledge-sharing: write up a learning or experience for the website / socials
  (LinkedIn, Medium, Twitter) — credibility, not promo.
- ~15–25 min follow-ups + log the numbers.

Batch sourcing weekly (20–25 prospects at once) so daily work is execution, not setup.
Content-sharing is a slow-burn credibility hedge; cold email is the near-term engine.
Expect roughly one paying client per 20–40 well-targeted, personalized sends.
