"""The one number every layer of `ask` agrees on.

⭐ Here **only because they are shared** (ADR-325). `_HORIZON` is read by the parsers, the deciders, the context
and the entry points alike, so it cannot live in any of them without making that one the others'
dependency.

⚠️ `_TIE_BREAK` started here and moved to `deciders`, where its only caller is: a source-scanning guard
resolves `**_TIE_BREAK` by finding the definition in the same file, and the move broke it.
"""



_HORIZON = 5   # transfer/analyse are multi-week decisions (captain is next-GW)

