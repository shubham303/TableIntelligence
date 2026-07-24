# LinkedIn

## The principle
LinkedIn is the one platform in this set where **self-promotion is allowed and
expected.** Your feed is yours. But "allowed" is not "unlimited" — the posts
that perform are value-first (insight, story, number) with a product mention
that fits, not pitch-first. The hook has to deliver; clickbait that doesn't
land costs you trust and reach.

## Structure
- **Your feed** — your posts (text, image, document/carousel, video).
- **Post** — your original content (kind=`author`).
- **Comments on others' posts** — possible but lower priority (kind=`reply`).

You primarily **AUTHOR** posts on your own feed.

## Self-promotion policy
**Allowed.** Mentioning your product, linking to it, sharing wins, and asking
people to try it are all normal on LinkedIn. The guardrail is *quality*: lead
with insight or story, make the product fit the story, don't make every post a
pitch.

## Format constraints
- **Text or Markdown-ish** (LinkedIn renders plain text + emoji + line breaks;
  no real markdown). `content_format='text'` is safest; the agent should keep
  formatting to line breaks and emoji, not headers/code blocks.
- **Hook in the first 2–3 lines** ("see more" truncates). Lead with a number,
  a question, or a contrarian-but-honest take.
- **Length:** 150–500 words for a thought post; shorter (1–3 lines) for
  one-liners. Carousels/documents are separate formats the harness would
  assemble.
- **3–5 hashtags** at the end, relevant and specific over generic.

## Recency window
- N/A for your own feed (you're publishing, not replying).
- For **comments on others' posts**: ≤7 days, and only where you add real
  value (don't hijack).

## Do's and don'ts
**Do:**
- Hook → story/insight → CTA. One idea per post.
- Use specifics: real numbers, real moments, real lessons.
- Vary the hook (RULE A — dedup against prior posts).
- End with a single, clear CTA (or a question to drive comments).

**Don't:**
- Write clickbait the body doesn't deliver — it tanks the post and your reach.
- Stack 10 hashtags. It looks desperate and LinkedIn deprioritizes it.
- Cross-post the exact same text daily. Vary it.
- Pitch in every single post. Mix value posts with product posts.

## Data inputs for the agent
- Authoring is the main mode: `social_add_post(..., platform='linkedin',
  kind='author', content=<post>, content_format='text')`.
- If replying to others' posts: `search_type` would be `find_posts`,
  `scopes` = handles; `kind='reply'`, `target_kind='linkedin_post'`.

## Pitfalls & honesty caveats
- **The algorithm rewards dwell time and conversation.** A post that gets
  comments (especially substantive ones) gets shown more. End with a question,
  not just a link.
- **"Broetry" (the one-sentence-per-line engagement-bait style) works but
  reads as manipulative.** Use it sparingly or not at all — the template's
  tone rule decides.
- **Claims about outcomes must be honest.** "We grew 10x" must be true.
  LinkedIn isn't regulated like an ad, but your reputation is.
