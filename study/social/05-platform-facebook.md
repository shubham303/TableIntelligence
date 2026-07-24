# Facebook

## The principle
On Facebook, **groups are where it happens.** The organic feed of a page is
near-dead for most creators; the real conversations are inside niche groups
where members help each other. Treat each group as its own country with its
own laws. Many groups forbid self-promotion entirely or restrict it to a
specific pinned thread or day. When in doubt, be helpful, don't pitch.

## Structure
- **Group** — a community (you join it; it has rules and admins).
- **Group post** — a post inside the group (kind=`author` if you make one).
- **Comment** — a reply to a group post (kind=`reply`).

You primarily **REPLY** to existing group posts (helpful answers), and
occasionally **AUTHOR** a group post (a question or a genuine share, if the
group allows it).

## Self-promotion policy
**Group-dependent — often restricted.**
- Many groups ban links and self-promo entirely, or confine them to a weekly
  "self-promo thread." Read the group rules.
- Even where allowed, a group post that's a pitch will get you removed.
- The safe default: **be a helpful participant.** Mention the product only if
  directly asked, and only if the group permits it.

## Format constraints
- **Text.** `content_format='text'`.
- Group posts can be longer than tweets but should still be scannable.
- Comments: a few sentences to a paragraph. Reference the OP's situation.

## Recency window
- For **comments/replies**: **≤7 days.** Active group posts age similarly to
  reddit threads.
- For your own group posts: n/a (but check if the group allows them).

## Do's and don'ts
**Do:**
- Read the group rules before posting anything. This is non-negotiable.
- Match the group's tone — a B2B SaaS group ≠ a hobbyist group.
- Answer the OP's actual situation with specifics.

**Don't:**
- Drop your link in a comment or post unless the rules explicitly allow it.
- Cross-post the identical message to multiple groups.
- DM members out of the blue (against FB rules and creepy).

## Data inputs for the agent (search spec)
- `platform`: `facebook`
- `search_type`: `find_threads` (or `find_posts`)
- `scopes`: group names or IDs
- `queries`: topics/questions
- `recency`: `7d` (default)
- `keywords`: product/audience terms

For group posts: `social_add_post(..., platform='facebook', kind='author',
content=<post>)`.
For comments: `social_add_post(..., platform='facebook', kind='reply',
target_url=<post url>, target_kind='facebook_post', content=<comment>)`.

## Pitfalls & honesty caveats
- **Group admins have absolute power and no sense of humor about spam.** One
  removal can burn the whole group for you. Be conservative.
- **"Helpful but with a link" is still self-promo.** If the rules forbid links,
  forbidding them means you, too.
- **Identity is real.** Facebook posts are tied to a person. Tone and
  honesty matter more here than on an anonymous platform.
