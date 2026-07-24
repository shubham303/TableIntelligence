# Content principles — the authoring craft

These apply across all platforms. The per-platform notes (01–05) refine them.

## RULE A — DEDUP before authoring (mandatory)
Before you draft any **original** post (kind=`author`), you MUST call:

```
social_list_posts(campaign_id, platform=<platform>, kind='author')
```

and read every prior post for that campaign + platform (any status). Then:

- **Don't reuse** an angle, hook, headline, or core takeaway already used.
- **Vary the framing** even on a recurring theme (e.g. if last week's LinkedIn
  post led with a number, this week lead with a question or a story).
- If the requested topic is **already well-covered**, say so and **propose a
  fresh angle** instead of repeating. Repetition reads as automation and tanks
  engagement.

This is the social equivalent of the outreach rule "vary the subject across a
batch." Replies (kind=`reply`) are exempt — each reply is tied to a unique
target_url, so there's no dedup question.

A cheap mental model: keep a running sense of "what we've already said here."
The dashboard list IS that memory — read it.

## RULE B — TOPIC INTAKE (when no topic is given)
When the user says "write a post / tweet / article" and gives no topic, ask
**one** batched question:

> "What's the topic — a rough writeup, an angle, or a draft? Or say 'you pick'
> and I'll derive one from the template."

- If they give a topic / rough / draft → use it.
- If they decline or say "you pick" → **derive** a topic from:
  1. the campaign's frozen template (product, keywords, audience, do's/don'ts), and
  2. recent feedback notes (`social_list_feedback`).
  Then **state your chosen topic + angle + which platform rule applies**
  *before* drafting. This keeps authoring grounded in what the campaign is
  actually about, and gives the user a chance to redirect cheaply.

Never author in a vacuum. A post unrelated to the product/audience the user
defined is a wasted post.

## The content principles (every platform)

### Helpful > promotional — everywhere, doubly on reddit/medium/FB
Even on LinkedIn/Twitter where self-promo is allowed, a post that *teaches
something* and mentions the product earns more than a post that pitches. On
no-self-promo platforms, the product should be invisible unless asked.

### One idea per post
Don't cram a product launch, a customer story, and a hiring announcement into
one post. Split them. One clean idea, one CTA (or none).

### Lead with the hook, deliver on it
The hook (first line / first 2–3 lines / first tweet) earns the click. The body
must deliver on the hook's promise. Clickbait that doesn't deliver costs trust
and reach.

### Vary opens across a batch
If you're drafting multiple posts for one platform, the openings must differ.
Identical openings across posts read as mass-produced. (See RULE A.)

### Recency first for replies
Only reply to recent posts: ≤7d forums, ≤3d Twitter, ≤14d Medium comments.
Old threads are dead threads. Engaging with dead threads is noise.

### Match the platform's native format
- Medium = long-form + headings + markdown.
- Twitter = ≤280 chars or a numbered thread.
- LinkedIn = hook + story + CTA + 3–5 hashtags.
- Reddit = a direct, correct, well-formatted answer.
- Facebook = a group-appropriate comment, group-rules-respecting.

### No link-dumping, no copy-paste
Never paste the same reply across threads. Never drop a bare link. If a link
is appropriate, wrap it in context.

### Honesty in claims
Numbers about your own product are claims you can stand behind. External or
competitive numbers are estimates — frame them as such. Don't fabricate
testimonials or outcomes.

## How these become prompts
- RULE A and RULE B are stated in the `social_agent` prompt's AUTHORING stage.
- This note (`06`) is referenced by that prompt as the canonical craft
  reference.
- The per-platform prompts (`social_platform_*`) layer platform specifics on
  top; on conflict the template wins, then this note, then the platform note.
