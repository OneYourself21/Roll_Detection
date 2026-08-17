# P6 — Window-Function Analysis & Columnar Runtime Check (DuckDB + Polars)

**Closes:** P5's deferred scope (window functions, roll-detection query) that got eaten by the ingest work.

## Objective

Redo P5's roll-detection reasoning as SQL window functions in DuckDB, run against the Parquet store, and use one controlled timing comparison against the equivalent Polars expression — with a context manager doing real lifecycle/timing work, not decoration.

## Deliverables

1. **Daily returns per contract/symbol**, computed with a window function (ordered frame, not a Python loop).
2. **Rolling stats** (your choice — rolling volatility or rolling volume is reasonable) using a windowed frame clause.
3. **Roll-detection query**: formalize P5's manual heuristic ("next contract's daily volume overtakes current front-month's, with a sustained margin to avoid flip-flopping") as a single window-function query instead of eyeballing/looping. This is the centerpiece — it should reproduce or improve on P5's findings, and you should be able to point at where they agree or diverge.
4. **One runtime comparison**: the same query (pick one — roll-detection is the natural candidate) expressed in DuckDB SQL vs. Polars, timed with a custom context manager. One comparison, not a suite — resist the urge to benchmark everything.
5. **Context manager**: at least one, doing something real — timing the query, or managing a DuckDB connection's lifecycle. Should demonstrate you understand `__enter__`/`__exit__` semantics, not just decorate a function with `@contextmanager` for its own sake.
6. **Findings note** (GitHub, like P4/P5): roll-detection results vs. P5's, timing observations, and a stated (and justified) decision on the EST/UTC storage question — pick one, say why, move on.

## Standing Requirements (carried from every prior project)

- Full type hints on every function signature.
- Functions return; the `if __name__` block prints.
- No string-concatenated SQL if any query takes a parameter.
- Clean, honest commit history — no "final version."
- `.venv`, `__pycache__`, and the Parquet file itself stay git-ignored (already true in Parquet_Builder — keep it that way).
- Verify results by querying, not by eyeballing — if you claim the roll-detection query matches P5, show the comparison.

## Explicitly Out of Scope

- A general DuckDB-vs-Polars benchmark harness.
- Options data, other instruments — Nasdaq futures only, as your README already scopes.
- "Solving" the tz representation by avoiding the decision — document it either way.

## Definition of Done

Query results reproducible from a clean checkout, tz handling stated with reasoning (not silently inherited), timing comparison uses the context manager, standing rules pass, findings note committed.
