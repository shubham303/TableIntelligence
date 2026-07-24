# The feedback loop — how the agent learns (template always wins)

The whole point of capturing rejection reasons and notes is that **the next
run is better than the last one.** This note specifies the loop precisely.

## Step 1 — capture (the dashboard does it; the agent helps)
- When the user **rejects** a post in the dashboard, the UI asks for a reason
  and saves it as feedback (`kind='rejection'`, linked to the post).
- The agent can also capture feedback explicitly:
  `social_add_feedback(campaign_id, kind='rejection'|'note', reason=<short>,
  note=<long>, post_id=<optional>)`.
- A **rejection** is "this specific post is wrong because…"
- A **note** is a free-text preference ("I prefer shorter tweets", "don't use
  the word 'revolutionary'").

## Step 2 — read before every run (mandatory)
Before drafting anything in a run, call:

```
social_list_feedback(campaign_id)
```

Read every entry. Fold the rejections and notes into this run's drafting. The
feedback is *context for this run*, layered on top of the frozen template.

Examples of folding feedback:
- "too salesy on reddit" → make the reddit reply genuinely selfless; product
  mention removed.
- "tweets too long" → cap tweets shorter; prefer threads earlier.
- "don't mention competitor X" → never name X.

## Step 3 — the precedence rule (template wins)
Feedback is **advisory context for the run**, not a new authority. If a
feedback note **conflicts with the frozen template**, the **template wins.**

- Template says "always mention the demo link"; a note says "no links on
  reddit" → on reddit, follow the template? **No.** Wait — re-read: the
  template is the highest layer, but platform etiquette (no-self-promo on
  reddit) is a *platform* rule, and the template almost certainly didn't mean
  "violate platform rules." When in doubt: **state the conflict**, follow the
  higher layer, and propose a template change so the user can clarify.

The general rule: **template > agent instruction > platform instruction**, and
feedback sits *below* all three as run context. When feedback is durable and
generic, escalate it to a template change (step 4) rather than silently
applying it forever.

## Step 4 — propose template changes for generic, permanent feedback
Most feedback is about *one post*. But some feedback is a **rule that should
apply to all future work** ("never use exclamation marks", "always cite the
source", "our tone is casual not corporate"). For those, **don't** silently
edit the template — **propose** a change:

```
social_propose_template_change(
    template_id, change_kind='append'|'replace'|'add_rule',
    rationale=<why>, proposed_patch=<the text to add/replace>,
    source_feedback_ids=<the feedback that motivated it>)
```

The proposal is saved (status `proposed`). The user reviews it in the
dashboard (or via `social_list_template_changes`) and approves or rejects it
(`social_update_template_change(change_id, status='approved'|'rejected')`).
Only after approval does `social_apply_template_change(change_id)` actually
patch the template.

**Why this dance?** The template is the user's curated playbook. Silently
mutating it from rejection-reasons would make it drift unpredictably and
become unauditable. Propose → approve → apply keeps the user in control and
the template legible.

## Step 5 — the loop closes
```
draft → review → reject (capture reason) → next run reads feedback →
  drafts improve → durable lesson → proposed template change →
  user approves → template improves → repeat
```

The agent that reads its own rejection reasons and varies its output accordingly
is the product. The agent that ignores feedback and writes the same rejected
post again is a bug.

## Honesty caveats
- **Don't overfit to one rejection.** A single user preference isn't a universal
  rule — fold it into the next run, and only propose a template change if it's
  clearly generic and permanent.
- **Don't propose a change for every note.** Most feedback is run-local.
  Reserve proposals for durable, cross-post rules.
- **The user can always edit the template directly** (`social_update_template`)
  for trivial fixes the user asked for in conversation. The propose→approve→
  apply path is for *feedback-driven* durable changes.
