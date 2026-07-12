---
name: data-teardown-outreach
description: >
  Find and win data-analysis clients for a solo consultant. Use this whenever the
  user wants to prospect for clients, find businesses to email, build a target list,
  run a "teardown" or free-sample analysis on a company's public data, or draft a
  cold email — a product-led service pitch backed by a one-line finding from public
  data. Cold email is the only outreach channel (social platforms are for
  knowledge-sharing, not ads). Trigger
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
the right businesses, run a "teardown" on their *public* data for one credible finding,
and draft a **product-led cold email** — pitch the service first, back it with that
one-line finding, and point to a credibility website. The operator (Shubham) reviews
every finding and sends every message by hand — this skill produces **drafts and
analysis**, never auto-sends.

## The business this serves (context)

The operator sells data-analysis-as-a-service: he takes a client's messy data (sales,
orders, marketing, donations, etc.) and produces reports with genuine, revenue-driving
insights. The go-to-market is **service-first**: land clients by doing a free sample
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
2. **Run a teardown** — pull the prospect's *public* data and compute real findings
   (deterministically, in code — see guardrails). You only need **one** for the email.
3. **Draft outreach** — a **product-led cold email**: pitch the service first, back it
   with one sentence of proof from the teardown, and point to the credibility website in
   the signature. No pricing in the body — the ask is just "let's get in touch".
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
lead; an ops finding → the COO). For each, get a **named human + their email**:
- **LinkedIn** — find the people and their titles; note who owns which area.
- **Company site** — About / Team / Leadership / Contact pages often list names and
  sometimes direct emails.
- **Email patterns** — if a company email format is visible (e.g. `first@domain`,
  `first.last@domain`), infer the likely address for a named person, and verify with a
  free checker where possible. Prefer a **named human over `info@`** every time.
- Log **2–4 contacts per prospect** in the tracker so a single non-reply doesn't kill the
  lead — you can reach a second decision-maker. Don't blast the same email to all of them
  at once; space them, and tailor the finding to each person's area.

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

**Product-led, ≤4 sentences, two short paragraphs.** The motion is **service pitch first,
one-line proof second**, with a credibility website in the signature doing the real
convincing (blogs/Medium/Twitter/LinkedIn all point back to it). No methodology paragraph,
no credential dump, no pricing in the body. Structure:
1. **Paragraph 1 — the service pitch.** "I saw you run [Brand] — extracting insight as an
   ecommerce brand grows is hard, expensive, time-consuming. **I provide a service** that
   uses AI agents to do exactly that." Say *provide a service*, never "built a product".
2. **Paragraph 2 — one-line proof + soft ask.** "From the public data available about your
   [store/site], I found [ONE-SENTENCE finding, tied to money or a decision]. If you think
   it's worth your time to see how I can help you, let's get in touch." The finding is a
   *single sentence* — enough to prove you looked, not a teardown.
3. **Signature**: clickable-name link + website — and **only** the website. The signature
   must contain `shubhamrandive.com` and no other link (no LinkedIn, Calendly, Medium,
   Twitter, email URLs, etc.):
   `[Shubham Randive](https://shubhamrandive.com) · shubhamrandive.com`. The site is live,
   so link the name to it; every other profile is reachable from the site.

**Do NOT** put pricing or the sample-then-paid model in the body — the ask is just "let's
get in touch"; the service/pricing come out on the call or the website. Match the promised
depth to the prospect's tier (from Step 1) only once you're talking, not in the cold email.
Keep the subject plain + benefit-led (e.g., "Getting real insight out of your store's
data"), not a naked finding.

See `references/outreach-templates.md` for the ready template and the reusable principles.

---

## Step 4 — Hand off for review & send

**Persist every teardown to disk** so the batch is reviewable and reusable. Write one
Markdown file per client under a date-stamped folder at the project root:

```
.claude-artifacts/teardown-outreach/<YYYY-MM-DD>/<client-slug>.md
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
