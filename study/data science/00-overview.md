# Data Science in this engine — the map

Read this first. It explains the philosophy, lists the algorithm families in study
order, and tells you how to read every other note in this folder.

## The one idea that governs everything
**Deterministic math computes every number; the LLM only writes prose around those
numbers.** Nothing in `src/tabular/analytics/` asks a language model "what's the
correlation?" — it runs scipy/scikit-learn/statsmodels, gets an exact number, and the
number is what a client sees. This is the whole credibility model of the business: a
figure in a report can always be traced to a computation, never to a guess.

Practical consequence for you: to sell this, you must understand *what each computation
means and when it's valid* — because the LLM won't catch a misapplied test, but a client's
in-house analyst will.

## The families, in study order (matches the file numbers)
| # | File | Family | Core question it answers |
|---|------|--------|--------------------------|
| 01 | descriptive | **Descriptive stats** | "What does this column look like? Any weird values?" |
| 02 | association | **Association & hypothesis testing** | "Are these two things related, and is it real (not luck)?" |
| 03 | compare | **Group / period comparison** | "Did this metric actually change vs before?" |
| 04 | cohort | **Segmentation (RFM) & retention** | "Who are my customers and do they come back?" |
| 05 | clustering + dimreduction | **Unsupervised learning** | "What natural groups exist without me labelling them?" |
| 06 | basket | **Association-rule mining** | "What gets bought together?" |
| 07 | timeseries | **Time series** | "What's the trend, what's next, when did it break?" |
| 08 | supervised | **Supervised learning** | "Can I predict Y from X?" |
| 09 | interpretation + insights | **Model interpretation & key-drivers** | "*Why* did the model / metric do that?" |
| 10 | causal | **Causal inference** | "Does X *cause* Y, or just correlate?" |

Difficulty climbs roughly top-to-bottom. 01–04 are things a sharp analyst does in a
spreadsheet; 05–10 are where "data science" earns its name.

## Two axes to keep in your head
1. **Descriptive → Predictive → Causal.** Describe what happened (01, 03, 04, 07),
   predict what will happen (07 forecast, 08), explain what *causes* it (10). This axis
   measures **analytical depth** — how sophisticated the *question* is. It rises
   left-to-right. **But depth is not the same as value** (see the value note below).
2. **Supervised vs unsupervised.** Supervised needs a labelled target column you want to
   predict (08). Unsupervised finds structure with no target (05, 06). Segmentation (04)
   is rule-based, not learned — don't confuse it with clustering (05).

## Where the value actually is (read this twice)
There are **two independent axes of value**, and conflating them is a costly mistake:

- **Analytical depth** (descriptive → predictive → causal) — how hard the *question* is.
- **Labour displaced** — how much human time and skill the agent replaces to produce the
  answer *correctly and repeatably*, month after month.

Rough model: **value ≈ depth × labour displaced × how much the client needs it.**

The trap: assuming value only lives at the predictive/causal end. It does **not**. The
agent delivers value at *every* level, because at all three a human would otherwise have to
take messy exports, reconcile them, clean them, know what to compute, and do it again next
month without error — and that cleanup is ~70–80% of any real analysis; the statistic is
the last 5%.

So the tiers monetize in **different shapes**, not different amounts:
- **Descriptive** — *low depth, high labour displaced, needed by 100% of clients.* Sells on
  **toil removed**: "trustworthy numbers from your mess, every month, without your team
  touching a spreadsheet." Low-drama, works on small data, and it's the gateway that makes
  the higher tiers even runnable (nothing models well on dirty data).
- **Predictive** — *higher depth.* Sells on **foresight** (who'll churn, what's next).
- **Causal** — *highest depth.* Sells on **"only you can do this responsibly"** (attribution).

Pitch descriptive on the *outcome and the hours saved*, never as "I compute averages"
(that sounds like a spreadsheet). The AI doing messy → structured → insight fast and
deterministically **is** the value, at all three levels.

## How to read each note
Every file has the same shape:
- **Intuition** — the idea in plain English.
- **The concept** — the actual statistics/ML, with the minimum math that matters.
- **In our engine** — the exact function, the library it wraps, the method chosen, and the
  key parameters. (Memory rule: we *wrap proven libraries*, we don't hand-roll algorithms.)
- **Reading the output** — what the returned numbers mean.
- **Assumptions & pitfalls** — when it's invalid or misleading. This is the part clients
  test you on.
- **Marketing / e-commerce angle** — the concrete way this earns money in your business.

## A note on the `Result` object
Every function returns a `Result` with `method`, `summary` (one human sentence), `values`
(the numbers), and `metadata` (the choices made + assumption checks). When you read the
code, `values` is the payload and `metadata` is the "show your work" audit trail — the
thing that lets a finding survive scrutiny.
