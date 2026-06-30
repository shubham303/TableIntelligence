# Adding an algorithm — the repeatable recipe

Follow these steps for every new function so the library stays coherent as it grows.

1. **Pick** the next unchecked item from the README roadmap.
2. **Research** it properly — understand the method, its assumptions, and when it's
   the *wrong* choice. Don't implement what you can't yet explain.
3. **Write the precondition** first: what must be true of the input data (dtypes,
   no missing values, minimum sample size, scaling). Encode it using the shared
   `validation/` helpers — do not re-implement dtype or assumption checks locally.
4. **Implement** using an existing, trusted library (scipy / scikit-learn /
   statsmodels / xgboost / etc.). The library does the math; your code does
   selection, validation, and packaging. Never compute statistics by hand.
5. **Return a `Result`** (or, for `train_*`, a `TrainedModel`). Populate `method`,
   `summary`, `values`, `metadata` (include the assumption-check outcomes that drove
   any choice). Keep `__repr__` readable.
6. **Materialize** any new data back as a column via `store.write_back_column`
   (e.g. cluster labels, predictions) so follow-ups become ordinary queries.
7. **Test** against the eval harness: add a fixture case with a known-correct answer.
   For deterministic methods, correctness is largely checkable — keep these strict.
8. **Document** the function and **check the box** in the README.

## Invariants to never break
- Structured returns, never print-and-return-None.
- Reuse `validation/`; never duplicate dtype/assumption logic.
- `store` is the only writer of columns.
- The method chosen and its assumptions are always reported in the result.
- Computation is deterministic; the same inputs give the same outputs.
