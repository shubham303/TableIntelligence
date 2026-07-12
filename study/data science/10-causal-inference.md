# 10 — Causal inference (the capstone)

Code: `analytics/causal.py` — `causal_effect`. Library: **DoWhy** (`CausalModel`:
identify → estimate → refute), optional `insights` extra.

This is the most advanced and most valuable family, because it answers the question every
other family *can't*: not "are X and Y related?" but **"if I change X, will Y actually
change?"** That's the question every business decision rests on.

## The core distinction (internalise this)
- **Correlation** (notes 02, 06, 09): X and Y move together. Could be X→Y, Y→X, or a hidden
  Z causing both.
- **Causation**: intervening on X *changes* Y.
The whole reason correlation ≠ causation is the **confounder** — a lurking variable driving
both. Ice-cream sales and drownings correlate; summer causes both. If you "cut ice-cream
sales" to stop drownings, nothing happens — you acted on a correlation.

## The gold standard, and why we need an alternative
The clean way to establish causation is a **randomised controlled trial / A-B test**:
randomly assign who gets X, so nothing else systematically differs, and any Y difference is
causal. When your client *has* run an A-B test, you're lucky — a simple comparison (note 03)
is already causal.
Often you only have **observational data** (they didn't randomise). Causal inference is the
set of methods that recover a causal effect from observational data *if* you can adjust for
the confounders — that's what `causal_effect` does.

## How `causal_effect` works — DoWhy's four steps
1. **Model** — declare `treatment` (the X you'd intervene on), `outcome` (Y), and
   `confounders` (common causes to adjust for; defaults to all other usable columns as a
   starting point).
2. **Identify** — use the **backdoor criterion**: figure out which variables must be
   controlled for to block the non-causal "backdoor" paths between treatment and outcome.
3. **Estimate** — fit the adjusted effect (`backdoor.linear_regression`) → a single number:
   the average causal effect of the treatment on the outcome.
4. **Refute** — the step that builds trust. It stress-tests the estimate (here: add a
   **random common cause** — a real effect should barely move when you inject noise). The
   `refutation` in the result reports whether the estimate survived. A number that collapses
   under refutation is not to be trusted.

## The load-bearing assumption (state it every time)
The estimate is only causal **if you've included the right confounders** ("no unmeasured
confounding"). If a real common cause is missing from the data, the number is biased and no
amount of math fixes it. So `causal_effect` is a *disciplined, refutable estimate*, not
proof — the default confounder set is a starting point to refine with domain knowledge, and
the honest framing to a client is "estimated effect, under these adjustments, and it passed
a refutation check." Overclaiming causation is the single most dangerous thing you can do;
this family's value is precisely that it lets you claim it *responsibly*.

## Marketing / e-commerce angle
Attribution — "did our work cause the lift?" — is every agency's weakest, most-disputed
claim, and it's exactly a causal question:
- **Olist worked example**: does **delivery running late**
  (`delivered − estimated` date) *cause* a lower **review score**, controlling for price,
  category, freight, region? A defensible causal answer → an ops recommendation with teeth.
- "Did the **site redesign** cause the conversion change, or was it seasonality?" — put the
  redesign as treatment, adjust for season/traffic-mix.
- "Does **email engagement** cause higher **repeat purchase**, or do loyal customers just
  open more emails?" (the classic confounded marketing claim).
Being able to say "we *estimated the causal effect* and it survived a refutation test,"
rather than "it correlates," is the most senior-analyst thing in your whole toolkit — and
the thing an agency literally cannot do by hand.
