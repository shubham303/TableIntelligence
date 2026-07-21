---
name: website-article
description: >
  Write and publish a blog article on Shubham's personal website
  (shubhamrandive.com, an Astro site in the sibling repo `shubham-site`). Use this
  whenever the user wants to turn something into a public post: a lesson learned, a
  method or paper worth sharing, an opinion/essay, a build-log, or — most often — a
  shareable write-up of a data analysis they just ran on a new dataset ("share this
  report", "write this up as an article", "turn this analysis into a blog post",
  "write a post about X", "publish this to my site"). It captures the site's house
  style and frontmatter, enforces the public-data-only privacy rule for analysis
  posts, and handles the full loop: draft in the site's voice → save to the blog
  collection → build → commit → push. It does NOT do outreach or client prospecting
  (that's data-teardown-outreach).
---

# Website Article

Write a blog post for **shubhamrandive.com** that sounds like Shubham wrote it, drops
cleanly into the Astro blog collection, and goes live with a commit and push. Two of the
most common inputs are **a lesson learned** and **a shareable version of a data analysis**
run on a new dataset — but any essay, opinion, or build-log fits.

The whole job is: understand what the user wants to say → write it in the house voice →
place it correctly → verify it builds → commit and push. Optimise for a post that reads
like a person thinking clearly, not a content-marketing listicle.

---

## Where the site lives

The website is a separate **Astro** repo, normally a sibling of this project:

- **Path:** `../shubham-site` (i.e. `/Users/shubhamrandive/Documents/codes/shubham-site`).
- **Remote:** `git@github.com:shubham303/shubham-site.git`.
- If the directory is missing, clone it into the parent dir first:
  `git clone git@github.com:shubham303/shubham-site.git`.
- Posts live in **`src/content/blog/`**, one Markdown file per post. Deploy is automatic
  on push (Vercel), so pushing to `main` publishes.

**Always read 1–2 recent posts in that folder before writing** — the voice guidance below
is the reference, but live posts are ground truth. Match them.

---

## Step 1 — Pin down the post

Before writing, be clear on three things (ask the user only if genuinely unknown):

1. **What's the one idea?** Every good post here makes a single point and earns it. If you
   can't say it in a sentence, the post isn't ready. (e.g. "The method that *changes the
   decision* is usually simpler than the one that looks impressive.")
2. **What type is it?** This sets the shape:
   - **Analysis / worked example** — you ran an analysis and want to share the finding.
     See the privacy rule in Step 2 and the structure in `references/style-guide.md`.
   - **Essay / opinion** — a point of view about how to work, think, or build.
   - **Build-log / lesson** — "I built/learned X, here's what surprised me."
3. **Who's it for and what should they feel?** Default reader: a smart practitioner or a
   potential client who'll respect being treated as intelligent. No fluff, no hype.

---

## Step 2 — Privacy & honesty guardrails (non-negotiable)

- **Analysis posts use PUBLIC or open data only.** Never publish analysis of a client's,
  employer's, or any private dataset. If the real work was on private data, reproduce the
  *shape* of the finding on a public/open dataset and say so explicitly — mirror the
  existing convention with a leading blockquote note, e.g.:
  > Worked example on a **public, open dataset** — no client or private data. This is the
  > shareable version of the kind of analysis I run privately on real store data.
- **Strip PII and third-party identifiers.** No real prospect names, personal emails, or
  private company specifics. Anonymise ("a coffee roaster", "an agency I contacted")
  unless the entity is public and the mention is clearly fair.
- **No invented numbers.** Every figure must come from the actual data or be clearly
  framed as illustrative. Don't fabricate results to make a cleaner story.
- **Claims stay honest.** Hedge what's uncertain; don't oversell. The brand is earned
  trust (see the site's "writing in public" post), and one inflated claim spends it.

---

## Step 3 — Write it in the house voice

Full style guide with do/don't examples: **`references/style-guide.md`**. The essentials:

- **One idea, argued in prose.** Short paragraphs, plain sentences. Lists are for genuine
  enumerations, not as a substitute for thinking. Prefer flowing paragraphs over bullet
  dumps.
- **Conversational but sharp.** First person. Direct address ("you"). Contractions. It
  should read like a smart friend explaining something, not a whitepaper.
- **Bold sparingly** — one or two key phrases per section, to carry the argument, not to
  decorate. Use `*italics*` for emphasis and `inline code` for technical terms.
- **Open with the problem or a concrete hook, not a definition.** Land the payoff by the
  end of the intro; don't make the reader wait.
- **End on the durable takeaway**, ideally a reframed one-liner the reader remembers.
- **Length:** as long as the idea needs and no longer — most posts here are ~400–900
  words. Cut anything that doesn't serve the one idea.

---

## Step 4 — Frontmatter & file placement

Every post is a Markdown file in `src/content/blog/` with this exact frontmatter schema
(from `src/content.config.ts` — `title` and `date` required, `description` optional but
always include it):

```markdown
---
title: "Sentence-case, specific, no clickbait"
date: YYYY-MM-DD
description: "One line that says what the reader gets. Shown in listings and meta tags."
---
```

Rules:
- **Filename = slug**, kebab-case, descriptive: `what-rfm-reveals-on-public-data.md`.
  Check the folder first so the slug is unique and consistent with siblings.
- **Do NOT add an H1 (`# Title`) in the body** — the layout renders the frontmatter
  `title` as the page heading. Start the body with the intro (or the privacy blockquote
  for analysis posts). Section headings start at `##`.
- **`date`** is the publish date (today unless the user says otherwise). Use the real
  current date.
- **Close with the site's CTA convention** when a hook fits: a short italic sign-off
  inviting contact, matching existing posts, e.g.
  `*...if it resonates, [get in touch](mailto:randiveshubham3@gmail.com).*`
  Do **not** self-link to shubhamrandive.com from within the site.

---

## Step 5 — Build, then commit & push

From the `shubham-site` repo:

1. **Build to verify** it compiles and the post renders:
   `npm run build` — confirm the new `/blog/<slug>/` page appears and there are no errors.
2. **Stage only the new/changed post** (and any intentional asset). Leave unrelated
   uncommitted changes alone — check `git status` first and don't sweep up files you
   didn't touch.
3. **Commit** with a clear message, e.g. `blog: add post on <topic>`, and include the
   standard co-author trailer.
4. **Push to `main`** — this triggers the Vercel deploy. Tell the user it'll be live
   shortly at `shubhamrandive.com/blog/<slug>/`.

Show the user the draft (or a tight summary + the file path) before pushing if the content
is substantial or you're unsure — publishing is public and outward-facing.

---

## Quick checklist

- [ ] One clear idea, stated in a sentence.
- [ ] Read a recent live post; voice matches.
- [ ] Public/open data only; PII stripped; no invented numbers.
- [ ] Frontmatter valid (`title`, `date`, `description`); **no body H1**.
- [ ] Unique kebab-case slug in `src/content/blog/`.
- [ ] `npm run build` passes; page renders.
- [ ] Only intended files staged; committed; pushed to `main`.
