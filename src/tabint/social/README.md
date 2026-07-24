# Social-Content Agent

> Build awareness for a product or project across social platforms — by drafting
> ORIGINAL content to publish (LinkedIn posts, Medium articles, tweets, Facebook
> group posts) AND by finding RECENT posts/threads/articles to reply to helpfully
> (reddit comments, Medium comments, tweet replies, FB group replies). The
> AI-agent **harness** (not this agent) discovers the posts and publishes them.

This is the **vision document** for the social-content agent. Unlike the
`seo_agent` (which ships as a scaffold), this agent ships **fully tooled**: a
`social_*` CRUD surface over the user's account, the `social_agent` prompt,
five platform prompts, and the `study/social/` knowledge base.

This agent is **one component** of a larger system. Per the governing principle
in `AGENTS.md` — **own the read, defer the write** — applied here as:

- **Reads we DEFER to the harness.** Discovering recent reddit threads, Medium
  articles, tweets, and FB posts is a read, but those sources are too varied
  and too vendor-specific for us to own. Instead the agent emits structured
  **search specs** (platform, queries, scopes, recency, keywords) saved to the
  dashboard; the **harness** runs them with whatever web-search / reddit /
  scraper tools the user has and hands the results back. This keeps the agent
  vendor-neutral and avoids baking brittle per-platform scrape code into a
  deterministic engine.
- **Writes we DEFER to the harness.** Posting a LinkedIn update, publishing a
  Medium article, sending a tweet, replying on a reddit thread, posting in a
  Facebook group — these mutate external systems the user owns and picks the
  vendor for. The agent drafts the content (+, for replies, saves the target
  URL and the exact reply text); the user copies/pastes or the harness's own
  browser/social tools post it. Mirrors the outreach agent's "we don't send
  email."

If you want the reasoning behind every platform, read `study/social/00-overview.md`
first, then 01–07 in order. This README is the *what* and *why*; the notes are
the *how*.

---

## The thesis

The market has infinite social scheduling tools and almost no one who turns
"build awareness for my product" into *the right content on the right platform,
varied, recent, non-spammy, and improving over time.* The gap is the loop:

```
  read feedback -> derive topics (template-grounded) -> discover recent targets
       -> draft varied, platform-correct content -> review
       -> publish (user/harness) -> capture rejection reasons
       -> propose template changes -> repeat, better
```

This agent owns the **reasoning + drafting** half. The **discovery** (running
the search specs) and the **publishing** are the **harness's** job, using
whatever tools the user has. The closed loop only exists when the harness wires
both halves together — this agent never scrapes or posts on its own (mirrors
the outreach agent's "we don't send email").

---

## The three-layer instruction model (precedence)

The agent runs on three stacked layers of instruction. **On conflict, the
higher layer wins.** Always state the conflict and follow the higher layer.

1. **USER TEMPLATE** (highest). The frozen campaign `prompt` — product,
   audience, keywords, do's/don'ts, tone. The user's curated playbook. This
   *always wins*.
2. **AGENT INSTRUCTION.** The `social_agent` prompt — the workflow, the
   authoring rules (dedup, topic intake), the content principles, honesty.
3. **PLATFORM INSTRUCTION.** One `social_platform_*` prompt per platform
   (`social_platform_reddit/_medium/_linkedin/_twitter/_facebook`) plus the
   matching `study/social/0N-*.md` note. Format, length, structure, etiquette.

The agent loads the relevant platform prompt before working on that platform
and folds its rules on top of the template.

---

## The platform matrix

| Platform | Structure | Self-promo? | Content unit | Recency (replies) |
|---|---|---|---|---|
| **Reddit** | subreddits → threads → comments | **No** (bans, shadowbans) | comment (reply) / text post (rare) | ≤7d |
| **Medium** | publications → articles → responses | Limited (case study, not sales) | article (author) / response (reply) | ≤14d |
| **LinkedIn** | your feed → posts | **Yes** (expected) | post (author) | n/a (your feed) |
| **Twitter/X** | tweets + threads; replies | Yes (own feed), careful (replies) | tweet/thread (author) / reply | ≤3d |
| **Facebook** | groups → posts → comments | Group-dependent, often restricted | group post (author) / comment (reply) | ≤7d |

The single biggest mistake on social is treating every platform the same.
Reddit is not LinkedIn. The per-platform notes exist because structure,
etiquette, and format differ — and getting any of them wrong gets you ignored
or banned.

---

## The two authoring rules (apply every time)

- **RULE A — DEDUP.** Before drafting an original post, scan prior posts for
  that campaign+platform (`social_list_posts(..., kind='author')`) and don't
  reuse an angle/hook/headline. Vary framing on recurring themes.
- **RULE B — TOPIC INTAKE.** When asked to "write a post" with no topic, ask
  once; if the user says "you pick," derive a topic from the template + recent
  feedback and state it before drafting. (See `study/social/06-content-principles.md`.)

---

## Scope: reads we defer, writes we defer

This agent is **one component** of a larger system the AI-agent harness
assembles.

| Capability | Ours? | Where it lives |
|---|---|---|
| Social knowledge base + the playbook | ✅ ours | `study/social/` + this package's prompts |
| `social_*` tools (templates, campaigns, search specs, posts, feedback, template-change proposals) | ✅ ours | this package's `tools.py` + `integration/service/platform.py` |
| **Discovering** recent posts/threads/articles | ❌ harness (read) | the harness's web-search / reddit / scraper tools — we emit **search specs** |
| **Posting/publishing/replying** on any platform | ❌ harness (write) | the user/harness's browser or social tools — we draft content + save targets |
| **Outreach / analysis / seo** | ❌ independent agents | `tabint.outreach` / `.analysis` / `.seo_agent` — the harness composes them |

**Net effect:** the social agent stores templates/campaigns, emits search specs
(reads the harness runs), stores drafted posts + replies, and captures feedback.
The harness discovers the content and publishes it. With no discovery/publish
tools connected, the agent still drafts varied, platform-correct content — the
user just finds the targets and publishes manually.

---

## The honesty boundary

The agent **drafts** content and **emits search specs**. The user/harness
**publishes** and **discovers**.

- **Never** post, publish, tweet, reply, comment, or DM on any platform.
- **Never** scrape platforms — emit search specs; the harness runs them.
- **Never** automate engagement, run bots, buy followers/likes, or mass-post
  the same content. No spam, no astroturfing.
- **Recency is mandatory for replies.** Dead threads are noise.
- **Helpful > promotional**, everywhere — doubly on reddit/Medium/FB.
- **The template wins on conflict.** Never silently edit it — propose changes,
  let the user approve.

---

## Status

**Implemented (this package):**
- `study/social/` — the knowledge base (00–07).
- `social_agent` prompt + 5 `social_platform_*` prompts (`prompts.py`).
- 25 `social_*` tools (`tools.py`): templates, campaigns, search targets,
  posts (author + reply, with dedup filters), feedback, template-change
  proposals, and `social_how_it_works`.
- Platform client in `integration/service/platform.py` (`/api/social/*`).
- Wired into the MCP server (`app/mcp_server.py`).

**Not ours (the harness owns):** platform discovery (running search specs) and
publishing (posting/replying). Deliberately not implemented here.

---

## Relationship to the other agents

**None, in code.** Per `AGENTS.md`, every agent is independent. The social
agent does not import or call the outreach, analysis, or seo agents, and they
do not depend on it. Where they cooperate, the harness composes them:

- **Building awareness** might pair with **outreach** (same product
  positioning → prospect emails). The harness drafts both; we don't.
- **Measuring what worked** (engagement → signups) is the **analysis** agent's
  job on exported data. The harness runs it; we don't.
- **SEO-driven content topics** could come from the **seo_agent**'s keyword
  research. The harness feeds them in as per-run instructions; we don't call
  it.

The social agent's contract is: **given a product template, emit search specs +
draft varied, platform-correct, non-spammy posts and replies, and learn from
rejections.** Everything beyond that is the harness composing other tools.
