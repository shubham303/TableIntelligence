"""Analysis db — DuckDB write mechanics only.

Pure storage primitives (the _ti_row table/view model, CSV load, write-back,
computed-column rebuild, derived-column registry). No knowledge of Session or
on-disk persistence — those live one level up in tabint.analysis.persistence.
"""
