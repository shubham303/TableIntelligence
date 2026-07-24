# Social-content for the agent — the map

Read this first. It explains the mental model the social-content agent runs
on, lists the knowledge areas in study order, the platform matrix, the
three-layer instruction model, the honesty boundary, and the feedback loop.

## The one idea that governs everything
**Awareness is earned by being useful where your audience already gathers —
not by shouting into the void.** The social-content agent does two things,
and they are different muscles:

1. **AUTHOR** original content to publish on your own channels (a LinkedIn
   post, a Medium article, a tweet or thread, a Facebook group post). This is
   where self-promotion is *allowed* (LinkedIn, your own Twitter feed) — but
   even there, value-first beats pitch-first.
2. **REPLY** to existing, *recent* posts where someone asked a question or
   made a point your product is genuinely relevant to (a reddit thread, a
   Medium comment, a tweet, a Facebook group post). Here you are a
   *participant*, not a marketer. On reddit and in most FB groups,
   self-promotion is penalized — be a genuinely helpful user first.

Both muscles share one rule: **recency + relevance + value, never spam.**
Replying to a 2-year-old thread, or pasting the same reply into ten threads,
is worse than doing nothing.

## The three-layer instruction model (precedence)
The agent runs on three stacked layers of instruction. **On conflict, the
higher layer wins.** Always say the conflict out loud and follow the higher
layer.

1. **USER TEMPLATE** (highest). The frozen campaign `prompt` — the product,
   audience, keywords, do's/don'ts, tone per platform. The user's curated
   playbook. This *always wins*.
2. **AGENT INSTRUCTION.** The `social_agent` prompt — the workflow, the
   authoring rules (dedup, topic intake), the content principles, honesty.
3. **PLATFORM INSTRUCTION.** The `social_platform_*` prompt for the platform
   you're working on, plus the matching note here (01–05). Format, length,
   structure, etiquette.

Load the platform prompt before working on that platform. Fold its rules on
top of the template. If a platform rule and the template disagree, the
template wins.

## The platform matrix (the cheat sheet)
| # | Platform | Structure | Self-promo? | Content unit | Recency (replies) | Honesty hot-spot |
|---|----------|-----------|-------------|--------------|-------------------|------------------|
| 01 | **Reddit** | subreddits → threads → comments | **No** — penalized (bans, shadowbans) | a comment (reply) / a text post (rare) | ≤7 days | "helpful user, not marketer" |
| 02 | **Medium** | publications/users → articles → responses | Limited — case study, not sales page | article (author) / response (reply) | ≤14 days (comments) | "substance, no drive-by links" |
| 03 | **LinkedIn** | your feed → posts | **Yes** — expected | post (author) | n/a (your feed) | "no clickbait that doesn't deliver" |
| 04 | **Twitter/X** | tweets + threads; replies | Yes (own feed), careful (replies) | tweet/thread (author) / reply | ≤3 days | "no hijacking, add value" |
| 05 | **Facebook** | groups → posts → comments | Group-dependent; often restricted to a pinned thread/day | group post (author) / comment (reply) | ≤7 days | "respect each group's rules" |

The single biggest mistake on social is treating every platform the same.
Reddit is not LinkedIn. A tweet is not a Medium article. The per-platform
notes (01–05) exist because the *structure, etiquette, and format* differ —
and getting any of them wrong gets you ignored or banned.

## The families, in study order
| # | File | Family | Core question |
|---|------|--------|---------------|
| 01 | reddit | **Reddit** | "How do I be helpful in a subreddit without getting banned?" |
| 02 | medium | **Medium** | "How do I write a real article and a substantive comment?" |
| 03 | linkedin | **LinkedIn** | "How do I write a post that earns attention, not eye-rolls?" |
| 04 | twitter | **Twitter/X** | "How do I fit a real idea into 280 chars, or a thread?" |
| 05 | facebook | **Facebook** | "How do I participate in a group without spamming?" |
| 06 | content-principles | **Authoring craft** | "How do I vary content, pick topics, and avoid duplicates?" |
| 07 | feedback-loop | **Learning** | "How do rejections/notes feed back in, and when do I change the template?" |

## How to read each note
Every platform note (01–05) has the same shape:
- **The principle** — the idea in plain English.
- **Structure** — the platform's content units (what is a "post", "thread",
  "comment", "group").
- **Self-promotion policy** — what's allowed, what's penalized.
- **Format constraints** — length, format (markdown/text), structure rules.
- **Recency window** — how old is too old to reply to.
- **Do's and don'ts** — the concrete etiquette.
- **Data inputs for the agent** — what the search spec looks like for this
  platform (`search_type`, `scopes`).
- **Pitfalls & honesty caveats** — where the agent must be careful.

## The honesty model
- **The agent never posts, publishes, replies, or scrapes.** It drafts content
  + saves reply targets; the user/harness publishes. (Mirrors the outreach
  agent's "we don't send email.")
- **No spam, no automation, no astroturfing.** Never paste the same reply into
  multiple threads. Never run engagement bots. Never buy followers/likes.
- **Recency is mandatory for replies.** Replying to dead threads is noise.
- **Helpful > promotional, everywhere — doubly so on reddit/Medium/FB.**
- **The template wins on conflict.** If a platform prompt says "use hashtags"
  but the user's template says "never use hashtags," the template wins.

## The two authoring rules (apply every time — see 06)
- **RULE A — DEDUP.** Before drafting any original post, scan prior posts for
  that campaign+platform (`social_list_posts(..., kind='author')`). Don't
  reuse an angle/hook/headline. Vary framing on recurring themes.
- **RULE B — TOPIC INTAKE.** When asked to "write a post" with no topic, ask
  once; if the user says "you pick," derive a topic from the template + recent
  feedback and state it before drafting.

## The feedback loop (see 07)
Rejections and notes are captured as feedback. The agent reads feedback before
every run. **Generic, permanent** feedback (a rule for all future work)
becomes a *proposed* template change the user approves — the template is never
silently mutated.

## Where the value actually is (read this twice)
There are infinite social scheduling tools and almost no one who turns "build
awareness for my product" into *the right content on the right platform,
varied, recent, non-spammy, and improving over time.* The closed loop is:

  **read feedback → derive topics (template-grounded) → discover recent
  targets → draft varied, platform-correct content → review → publish
  (user/harness) → capture rejection reasons → propose template changes →
  repeat, better.**

An agent that just writes ten identical LinkedIn posts is 90% of the way to
doing harm. The agent that varies, dedups, respects each platform, and learns
from rejections is the product.

## Relationship to the other agents
**None, in code.** The social agent does not import or call the outreach,
analysis, or seo agents. Where they cooperate, the harness composes them:
- Building awareness might pair with **outreach** (the harness drafts prospect
  emails from the same product positioning) — but that's the harness's call.
- Measuring what worked (engagement → signups) is the **analysis** agent's
  job on exported data — again, the harness wires it.
