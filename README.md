# karaka-lang

[![tests](https://img.shields.io/badge/tests-22%2F22%20passing-brightgreen)](tests/test_parser.py)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

A proof-of-concept for a **Paninian kāraka-based calling convention**:
predicate arguments are bound by grammatical role (agent, object,
instrument, recipient, source, locus) instead of by position, so argument
order is irrelevant to meaning. This directly targets a real usability
problem in positional logic languages (Prolog's arity/mode brittleness) and
compiles naturally to graph writes, since a role-labeled relation already is
a small labeled-edge structure.

📄 **[Read the write-up on Medium](https://joyboseroy.medium.com/i-used-a-2-500-year-old-sanskrit-grammar-to-fix-a-modern-programming-problem-3fbc4819b0b9)**:
the motivation, what earlier "Sanskrit programming language" attempts
missed, and a walkthrough of everything below.

This is **not** "Python with Sanskrit keywords," and it is **not** a claim
that Sanskrit is a superior general-purpose programming language. See
[`docs/DESIGN.md`](docs/DESIGN.md) for the full scope, honest limitations,
and prior-art review, and [`docs/position-paper.md`](docs/position-paper.md)
for the research framing.

## Quick example

```python
from karaka_lang import parse

# three different word orders, same meaning:
parse("robotah pakasthanam gacchati")   # robot-NOM kitchen-ACC go
parse("gacchati robotah pakasthanam")   # go robot-NOM kitchen-ACC
parse("pakasthanam robotah gacchati")   # kitchen-ACC robot-NOM go
# -> all three produce: Frame(gaccha, karma=pakasthan, karta=robot)
```

Roles resolve by suffix (`-aḥ` agent, `-am` object, `-ena` instrument,
`-āya` recipient, `-āt` source, `-e` locus, `-sya` possessor) rather than by
position:

```python
from karaka_lang import parse, to_prolog, to_cypher

frame = parse("manah ksetraya jalena jalasayat harati")
# man-NOM field-DAT flood-INS reservoir-ABL cause-harm
# -> Frame(hara, apadana=jalasay, karana=jal, karta=man, sampradana=ksetr)

print(to_prolog(frame))
# event(e1, hara).
# apadana(e1, jalasay).
# karana(e1, jal).
# karta(e1, man).
# sampradana(e1, ksetr).

print(to_cypher(frame))
# MERGE (e:Event {verb: "hara"})
# MERGE (n_man:Entity {name: "man"}) MERGE (e)-[:KARTA]->(n_man)
# ... etc, one MERGE per role
```

A small **Sūtra rewrite engine** implements Pāṇini's utsarga/apavada
principle (general rule, then a more specific exception overrides it).
Two versions exist: `SutraEngine` (manual integer priority) and
`SubsumptionEngine` (specificity *derived* from each rule's declared
condition set, which raises `AmbiguityError` instead of silently guessing
when two rules' conditions don't subsume one another), see
[`examples/arity_and_ordering_fixes.py`](examples/arity_and_ordering_fixes.py).

Arity beyond the six classical roles doesn't require more roles: any
role's value can be a nested `Frame` instead of a leaf string, and both
codegen targets recurse through it automatically.

## Real Paninian morphology (optional)

With `pip install vidyut`, the toy suffix table is replaced by actual
Ashtadhyayi derivation via [vidyut-prakriya](https://github.com/ambuda-org/vidyut).
Declined forms are generated through the real rule engine, and every
analysis carries its full sutra trace:

```python
from karaka_lang import VidyutResolver

r = VidyutResolver()
r.add_stems({"nara": "Pum", "grAma": "Pum", "aSva": "Pum"})

print(r.explain("aSvena"))
# aSvena = aSva + Trtiya (karana), derived by sutras:
#   1.2.45 -> 4.1.2 -> 1.3.7 -> 1.3.9 -> 1.4.13 -> 7.1.12 -> ... -> 8.4.68

frame = r.parse("naraH grAmam aSvena gacCati", verb_forms={"gacCati": "gam"})
# Frame(gam, karana=aSva, karma=grAma, karta=nara)
```

Closed lexicon by design (a symbol table), singular forms, default
vibhakti-to-karaka mapping. See `docs/ROADMAP.md` for what a full version
needs.

## Query mode

A role can be a variable. A frame with any variable compiles to a query
instead of a write, from the same `Frame` type:

```python
from karaka_lang import parse, compile_frame

compile_frame(parse("robotah pakasthanam gacchati"), target="cypher")
# MERGE (e:Event {verb: "gaccha"}) ...          <- assertion: a write

compile_frame(parse("?kah pakasthanam gacchati"), target="cypher")
# MATCH (e:Event {verb: "gaccha"})
# MATCH (e)-[:KARMA]->(:Entity {name: "pakasthan"})
# MATCH (e)-[:KARTA]->(k:Entity)
# RETURN k.name                                  <- question: WHO goes?

compile_frame(parse("?kah pakasthanam gacchati"), target="prolog")
# event(E, gaccha), karma(E, pakasthan), karta(E, K).
```

## Install

```bash
git clone https://github.com/joyboseroy/karaka-lang.git
cd karaka-lang
pip install -e ".[dev]"
pytest   # 22 tests (19 pass + 3 skip without vidyut)
```

If `pip install -e` fails with `missing the 'build_editable' hook`, your
`setuptools` predates PEP 660 support (added in `setuptools>=64`). Either:

```bash
pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"
```

or skip the install entirely and run everything with `PYTHONPATH` instead,
which always works regardless of `setuptools` version:

```bash
PYTHONPATH=. pytest
PYTHONPATH=. python3 examples/robot_kitchen.py
```

## Layout

```
karaka_lang/
  parser.py       -- tokenizer + karaka resolver -> Frame (nesting + ?variables)
  morphology.py   -- real Ashtadhyayi morphology via vidyut-prakriya (optional)
  sutra.py        -- SutraEngine (manual priority) + SubsumptionEngine
                     (derived specificity, AmbiguityError, nested-frame facts)
  codegen.py      -- Frame -> Prolog / Cypher, writes AND queries (compile_frame)
examples/
  robot_kitchen.py                  -- order-invariance demo
  rylands_fletcher.py               -- multi-role legal relation + rules + codegen
  arity_and_ordering_fixes.py       -- nested frames + subsumption + ambiguity
  real_morphology_and_queries.py    -- vidyut morphology with sutra traces + query mode
tests/
  test_parser.py                    -- 22 tests (3 skip without vidyut)
docs/
  DESIGN.md                         -- architecture, prior-art review
  ROADMAP.md                        -- beyond-toy status and what's next
  position-paper.md                 -- research framing, arXiv-style
  medium-article.md                 -- the published write-up
.github/workflows/tests.yml         -- CI: Python 3.10/3.11/3.12, with and without vidyut
```

## What this deliberately does not do

- **Sandhi segmentation.** Word boundaries here are whitespace. Real
  merged Sanskrit text needs
  [`vidyut-cheda`](https://github.com/ambuda-org/vidyut) or
  [`kmadathil/sanskrit_parser`](https://github.com/kmadathil/sanskrit_parser)'s
  dynamic-programming sandhi-split search. Planned; see `docs/ROADMAP.md`.
- **Verb-conditioned case mapping.** The vibhakti-to-karaka mapping is
  the default correspondence. Passives and verbs governing unusual cases
  break it; a per-verb table is the fix. See `docs/ROADMAP.md`.
- **Fully automatic rule-conflict resolution.** `SubsumptionEngine` derives
  specificity from each rule's *declared* condition set and correctly
  refuses to guess on genuine ambiguity, but those condition sets are
  still hand-written, not extracted automatically from arbitrary rule
  logic. See `docs/position-paper.md` §6.
- **Control flow.** This is a declarative/relational layer (facts + rules
  + queries, like Prolog), not a general-purpose imperative or functional
  language. Kāraka roles have nothing to say about loops or mutation.

## Status

v0.3.0. 22/22 tests passing (19 without vidyut installed; the 3
morphology tests skip cleanly). CI runs the suite on Python 3.10 through
3.12, both with and without vidyut. Real Ashtadhyayi-backed morphology,
nested-frame rule conditions, and query mode were added after the
initial release; `docs/ROADMAP.md` tracks what is done and what is next.
[Published on Medium](https://joyboseroy.medium.com/i-used-a-2-500-year-old-sanskrit-grammar-to-fix-a-modern-programming-problem-3fbc4819b0b9);
not yet submitted to arXiv or published to PyPI.

## License

MIT. See [`LICENSE`](LICENSE).
