# Medium

## The principle
Medium rewards depth. An article earns attention by having a real thesis and
delivering on it; a comment earns attention by adding substance the article
didn't. Medium is fine with you mentioning your product *as a case study or
example inside a substantive piece* — not as a sales page bolted onto a thin
article.

## Structure
- **Publication / user** — where articles live (your own profile, or you pitch
  a publication).
- **Article** — a long-form post (your original content, kind=`author`).
- **Response** — a comment on someone else's article (kind=`reply`).

## Self-promotion policy
**Limited and contextual.**
- In your **own article**: mentioning your product as a case study / example /
  "here's what we learned building this" is fine and normal. A pure sales page
  is not — Medium's distribution algorithms and readers both penalize it.
- In a **response/comment**: no drive-by links. Add real substance that
  engages with the article; if your product is relevant, a brief mention in
  context is OK, but the value must stand without it.

## Format constraints
- **Markdown.** `content_format='markdown'`.
- **Articles**: 600–1500 words typically. Clear title, a thesis in the first
  paragraph, H2/H3 subheadings, one CTA at the end (or none).
- **Comments/responses**: a few sentences to a couple of paragraphs.
  Reference the article's specific point; don't generic-praise it.

## Recency window
- For **comments/responses**: default **≤14 days.** Articles age slower than
  tweets; a 2-week-old Medium article may still be getting readers. Beyond 14
  days, only respond if the article is clearly evergreen and active.
- For your **own articles**: n/a (you're publishing, not replying).

## Do's and don'ts
**Do:**
- Write a real thesis. "Here's a problem, here's what we tried, here's what we
  learned" beats "here's our product."
- Use the product as *evidence*, not the subject.
- In comments, engage with a specific paragraph or claim from the article.

**Don't:**
- Drop your landing-page link in a comment with no substance.
- Write a "listicle" that's obviously SEO filler.
- Republish the same article text elsewhere without noting it (Medium's
  duplicate-content handling can hurt distribution).

## Data inputs for the agent (search spec)
- `platform`: `medium`
- `search_type`: `find_articles`
- `scopes`: publications or author handles to search
- `queries`: topics / questions from the template
- `recency`: `14d` (default for comments)
- `keywords`: product/audience terms

For original articles: `social_add_post(..., platform='medium', kind='author',
content=<markdown article>, content_format='markdown')`.
For comments: `social_add_post(..., platform='medium', kind='reply',
target_url=<article>, target_kind='medium_article', target_title=<title>,
content=<comment>)`.

## Pitfalls & honesty caveats
- **Distribution is gated by quality.** Medium's curators and the algorithm
  reward substantive, well-structured writing. Thin promo pieces get zero
  distribution — worse than not publishing.
- **Comments are public and permanent.** A dismissive or link-spammy comment
  reflects on the brand forever. Err toward substance.
- **Cite your own data honestly.** If you quote a number from your product,
  it's a claim about your product — fine — but frame external/competitive
  numbers as estimates.
