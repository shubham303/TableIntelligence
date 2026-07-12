# 06 — Association-rule mining (market basket)

Code: `analytics/basket.py` — `market_basket`. Library: **mlxtend** (`apriori` +
`association_rules`), optional `insights` extra.

## Intuition
"Customers who buy X also buy Y." Market-basket analysis mines the co-occurrence patterns
in orders to find product affinities — the engine behind "frequently bought together",
cross-sell, and bundling.

## The three numbers that define a rule
A rule is `antecedents → consequents` (e.g. {phone case} → {screen protector}). Judge it by:
- **Support** — fraction of all baskets that contain the whole itemset. "How common is this
  combo at all?" Filters out rare flukes (`min_support`, default 0.01 = 1% of orders).
- **Confidence** — of baskets with X, what fraction also have Y. "If they buy X, how likely
  is Y?" (`min_confidence`, default 0.2).
- **Lift** — confidence divided by Y's baseline rate. **The one that matters most.**
  - lift > 1 → X and Y appear together *more* than chance → genuine affinity.
  - lift = 1 → independent (no relationship).
  - lift < 1 → they *substitute* (buying X makes Y less likely).
Rules are ranked by lift, so the top rule is the strongest genuine affinity.

## How it works
The input is a tidy **order-lines** table (one row per item per order). The code groups
rows by the transaction column into baskets, one-hot encodes them (TransactionEncoder),
runs **apriori** to find frequent itemsets meeting `min_support`, then derives rules meeting
`min_confidence`, sorted by lift. A high-lift rule with decent support is a real,
actionable cross-sell.

## Pitfalls
- **Support/confidence tuning is everything.** Too-high support → only obvious best-sellers;
  too-low → thousands of noisy rules. Expect to tune per catalogue.
- **High confidence, low lift is a trap.** If Y is in 90% of all orders (a staple bag/box),
  almost any X → Y has high confidence but lift ≈ 1 — no real affinity. Always check lift.
- Apriori is combinatorial; huge, sparse catalogues get slow — raise `min_support`.
- Correlation, not causation (again): a rule is a pattern to exploit, not proof one product
  drives another.

## Marketing / e-commerce angle
- **Cross-sell / bundle recommendations** straight from the client's order history: "these
  two products have lift 3.2 — bundle them or recommend Y on X's page."
- **PPC/merchandising**: bid on or feature the high-lift pairs together.
- **Email flows**: post-purchase "you bought X, people love Y" using the top rules.
This turns an SEO/ads agency's flat product report into a revenue recommendation, which is
exactly the "one layer deeper" that justifies the fee. Needs enough orders to be stable —
an e-comm / retainer-tier tool, not for a 200-order shop.
