"""core — daftar's minimal core: the engine of the statement, beside today's gate (step 3 of the refinery, 2026-10-01).

The face is data, `core/law/core.yaml`, and the verbs beyond it are rows, `core/law/verbs.yaml`; the engine hardcodes
only what its twenty rules name. Everything else comes in through an interface: positions, quantities, protocols and
codes from the standards the release carries in core/law/ (systems, places, protocols, quantities and units,
registries; read by `core/standards.py`), and a garden's own kinds, levels, namespaces and flows as rows in its VOCAB.md.
Until v1 retires std-vocab, the rows it has are generated from it (`python3 core/translate.py law`), never typed.

    python3 core/check.py <garden>       # judge a garden written in statements
    python3 core/check.py --staged       # the index, and the commit's own rules: the pre-commit gate
    python3 core/check.py --law          # the law's own consistency: the face, the rows, the tables
    python3 core/install.py              # the core's gate as this clone's pre-commit (core/hooks/pre-commit)

A write is saved by today's `bin/dmsave.py`: it journals, writes each `at: now` as the moment of the heading it wrote
(the law clocks `at` as a moment), stages and commits, and the core's gate judges the commit.

Modules: `read` (a document, every key and value a string), `standards` (what outside standards say), `frame` (a
position in its system), `law` (the face and the rows, loaded and proved), `engine` (the rules), `commit` (the rules only
a commit shows), `check` (the command), `install` (the hook), `translate` (today's law and beans, in statements).
"""
