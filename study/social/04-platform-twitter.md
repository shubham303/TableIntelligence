# Twitter / X

## The principle
Twitter rewards brevity, timing, and personality. Your own feed is a place for
self-promotion (fine), but the platform's real social value for awareness is
**replying where you add value** — in active, recent conversations where your
product's domain is genuinely relevant. Hijacking threads or pasting the same
reply gets you muted/blocked fast.

## Structure
- **Tweet** — up to 280 characters (premium allows more; assume 280).
- **Thread** — a numbered sequence of tweets (when one isn't enough).
- **Reply** — a response to someone else's tweet (kind=`reply`).

Both `author` (your tweet/thread) and `reply` are common.

## Self-promotion policy
**Allowed on your own feed; careful in replies.**
- On your feed: pitch, share, link — normal.
- In replies: add value to *their* conversation. A light, relevant mention is
  OK; a sales reply under someone's tweet is spam and gets reported.

## Format constraints
- **≤280 characters** per tweet. `content_format='text'`.
- **Threads:** number each tweet (1/, 2/, … or 🧵). Keep each tweet
  self-contained enough to read in the timeline.
- No markdown rendering — plain text + emoji. Line breaks within a tweet are
  fine and often improve rhythm.

## Recency window
- For **replies**: **≤3 days**, ideally ≤24h. Twitter moves fast; replying to
  a week-old tweet is talking to an empty room.
- For your own tweets: n/a.

## Do's and don'ts
**Do:**
- Lead with the punchline/insight in the first tweet.
- For replies, engage with the specific point in the original tweet.
- Vary opens (RULE A — dedup).
- Use threads for substance that doesn't fit one tweet.

**Don't:**
- Exceed 280 chars in a single tweet (split into a thread instead).
- Reply with the same text under multiple tweets.
- Thread-hijack (replying with an unrelated pitch to borrow reach).
- Spam hashtags. On Twitter, 0–2 is normal.

## Data inputs for the agent (search spec)
- `platform`: `twitter`
- `search_type`: `find_tweets` (or `find_posts`)
- `scopes`: handles or hashtags
- `queries`: topics/questions
- `recency`: `3d` (default for replies)
- `keywords`: product/audience terms

For original: `social_add_post(..., platform='twitter', kind='author',
content=<tweet or thread>)`.
For replies: `social_add_post(..., platform='twitter', kind='reply',
target_url=<tweet url>, target_kind='tweet', target_author=<handle>,
content=<reply>)`.

## Pitfalls & honesty caveats
- **Engagement bait is penalized by users even when the algorithm rewards it.**
  "LIKE if you agree!" reads as low-value. Avoid.
- **Quote-tweeting a competitor critically can backfire** — it gives them
  reach. Engage on substance, not dunking.
- **A thread is a commitment.** If the idea is one tweet, don't pad it to
  seven. Each tweet in a thread should earn its place.
