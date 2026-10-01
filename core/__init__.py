"""core — daftar's minimal core: the engine of the statement, beside today's gate (step 3 of the refinery, 2026-10-01).

The face is data, `core/law/core.yaml`, and the verbs beyond it are rows, `core/law/verbs.yaml`; the engine hardcodes
only what its thirteen rules name. Everything else comes in through an interface: positions, quantities, protocols and
codes from the standards the release carries (`core/standards.py`), and a garden's own kinds, levels, namespaces and
flows as rows in its VOCAB.md.

    python3 core/check.py <garden>       # judge a garden written in statements
    python3 core/check.py --law          # the law's own consistency: the face, the rows, the tables

Modules: `read` (a document, every key and value a string), `standards` (what outside standards say), `frame` (a
position in its system), `law` (the face and the rows, loaded and proved), `engine` (the rules), `check` (the command).
"""
