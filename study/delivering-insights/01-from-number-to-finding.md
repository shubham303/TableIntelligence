# 01 — From a number to a finding

A statistic is not a finding. A finding is a number **plus context, plus a "so what," plus a
recommended action**, phrased for a decision-maker.

## The anatomy of a finding
`[Observation] → [why it matters / the money] → [recommended action] → [confidence/caveat]`

Weak: *"Repeat purchase rate is 22%."*
Strong: *"Only 22% of your customers buy again — below the ~30% typical for your category —
and closing that gap on last year's 4,000 buyers is roughly $X in repeat revenue. The 180
'At-Risk' customers (recent-but-slipping) are the fastest win; a targeted win-back is the
first move. (Based on your order history; worth validating against margin.)"*

Same number. The second is a decision.

## The rules

### 1. Lead with the "so what," not the method
Clients don't care that you ran a Kruskal-Wallis. They care that "mobile users from paid
social convert half as well as everyone else — that's where the budget is leaking." Method
goes in an appendix or the audit trail, never the headline. (Your engine already separates
`summary` from `metadata` for exactly this reason.)

### 2. Tie every finding to money or a decision
Run the "does this connect to revenue, cost, or a choice they'll make?" test on every line.
If not, cut it. This is the effect-size-over-p-value discipline (data-science note 02)
applied to communication: statistically real ≠ worth reporting.

### 3. Quantify the stakes
"Conversion dropped" → "conversion dropped 1.2 pts, ≈ $9k/month at current traffic." Put a
number on the opportunity so they can weigh your fee against it. This is what justifies the
price.

### 4. Always include a genuine positive
An all-criticism report reads as a manufactured sales pitch (it's in your outreach
guardrails too). One honest "here's what's working well" makes the whole thing read as
analysis and buys credibility for the critical findings.

### 5. Hedge honestly, and precisely
- Public/observational data → **hypothesis**: "worth checking against your numbers."
- Correlation → say "associated with," never "causes," unless you did the causal work
  (data-science note 10).
- Small sample → say so. Precise hedging *builds* trust; vague confidence destroys it.

### 6. One report, one headline
Pick the single most important finding and make it the spine. Supporting findings hang off
it. If everything is important, nothing is.

## The finding-writing loop
1. Compute (engine) → get the number + its metadata/limits.
2. Ask "so what?" until you hit a decision or a dollar figure.
3. Draft the finding in the anatomy above.
4. Red-team it: *Could this be seasonality? A confounder? Too small a sample? Am I claiming
   causation?* (data-science notes 07, 10, 08). Fix the claim to match what the data
   actually supports.
5. Add the honest caveat. Ship.
