# Reddit

## The principle
Reddit is a collection of communities (subreddits), not a marketing channel.
It rewards genuinely helpful users and punishes marketers — hard. The only
sustainable play is: **answer the actual question, fully and correctly, with
no thought of promotion.** If your product is truly relevant, someone will
*ask* you about it; then you may mention it, in a reply, once.

## Structure
- **Subreddit** (`r/<name>`) — a community with its own rules, mods, and tone.
- **Thread** (a post in a subreddit) — can be a question, a link, a text post.
- **Comment** — a reply to the thread, or to another comment (nested).

You primarily **REPLY** to threads (kind=`reply`). Original posts
(kind=`author`) are rare and only in subreddits that explicitly allow
discussion/showcase posts — check the rules first.

## Self-promotion policy
**No self-promotion.** This is the single most important rule on Reddit and
the one most often violated:
- Do **not** link your product, landing page, or demo unless directly asked.
- Do **not** say "I built X to solve this" unprompted.
- Do **not** paste the same answer across subreddits.
- Many subreddits have a ratio rule (e.g. <10% of your posts may be your own
  content) and mods will ban accounts that violate it. Some forbid links
  entirely.

Repeated self-promotion leads to downvotes, post removal, shadowbans
(your posts appear to you but are invisible to everyone else), and full bans.

## Format constraints
- Markdown (Reddit's own flavour). `content_format='markdown'` or `'text'`.
- No hard length limit, but **concise and scannable wins.** Lead with the
  direct answer; elaborate below.
- Use formatting (bullet lists, code blocks) only when it aids the answer.

## Recency window
- Default **≤7 days** for replies. The thread should still be active.
- Older threads (>7 days) are OK **only** if it's a high-traffic evergreen
  thread still getting fresh replies. Otherwise skip — you're talking to an
  empty room.

## Do's and don'ts
**Do:**
- Read the question carefully and answer *that specific question*.
- Be correct. If you're unsure, say so or skip.
- Match the subreddit's tone (r/devops ≠ r/Entrepreneur ≠ r/SaaS).
- Disclose any conflict of interest if it's genuinely relevant ("full
  disclosure: I work on something in this space").

**Don't:**
- Link-drop, pitch, or mention your product unprompted.
- Copy-paste the same reply across threads (mods spot this instantly).
- Reply to old/dead threads.
- Argue with mods. Ever.

## Data inputs for the agent (search spec)
- `platform`: `reddit`
- `search_type`: `find_threads`
- `scopes`: the subreddits to search (e.g. `["r/SaaS", "r/startups"]`)
- `queries`: sample questions / search terms from the template
- `recency`: `7d` (default)
- `keywords`: product/audience terms to match within results

When a found thread is relevant, draft a reply:
`social_add_post(campaign_id, platform='reddit', kind='reply', target_url=<thread>,
target_kind='reddit_thread', target_title=<thread title>, content=<reply>)`.

## Pitfalls & honesty caveats
- **Shadowbans are silent.** You won't know you're shadowbanned. The defense
  is behavioral: be a real user, don't mass-post, don't self-promote.
- **"Relevant" is not "promotional."** Your product solving the OP's problem
  does not license you to pitch it. Answer the question; the mention (if any)
  goes in a *reply to a direct question*, by the user, manually.
- **Each subreddit is a different country.** What's welcome in r/startups may
  be a ban in r/Entrepreneur. Read the rules.
