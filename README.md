# karaka-lang

A proof-of-concept for a **Paninian kāraka-based calling convention**:
predicate arguments are bound by grammatical role (agent, object,
instrument, recipient, source, locus) instead of by position, so argument
order is irrelevant to meaning. This directly targets a real usability
problem in positional logic languages (Prolog's arity/mode brittleness) and
compiles naturally to graph writes, since a role-labeled relation already is
a small labeled-edge structure.

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
when two rules' conditions don't subsume one another) — see
[`examples/arity_and_ordering_fixes.py`](examples/arity_and_ordering_fixes.py).

Arity beyond the six classical roles doesn't require more roles: any
role's value can be a nested `Frame` instead of a leaf string, and both
codegen targets recurse through it automatically.

## Install

```bash
git clone <this repo>
cd karaka-lang
pip install -e ".[dev]"
pytest   # 14 tests
```

## Layout

```
karaka_lang/
  parser.py   -- tokenizer + karaka resolver -> Frame (the AST, now supports nesting)
  sutra.py    -- SutraEngine (manual priority) + SubsumptionEngine (derived, with AmbiguityError)
  codegen.py  -- Frame -> Prolog facts / Cypher graph writes, recurses through nested frames
examples/
  robot_kitchen.py               -- order-invariance demo
  rylands_fletcher.py            -- multi-role legal relation + rule resolution + codegen
  arity_and_ordering_fixes.py    -- nested frames + subsumption engine + ambiguity handling
tests/
  test_parser.py                 -- 14 tests, all currently passing
docs/
  DESIGN.md                      -- architecture, prior-art review, roadmap
  position-paper.md              -- research framing, arXiv-style
  medium-article.md              -- accessible write-up
```

## What this deliberately does not do

- **Real Sanskrit morphology.** The suffix table here is a fixed toy
  (a-stem masculine only). Production morphology should bind to
  [`vidyut-prakriya`](https://github.com/ambuda-org/vidyut), which is
  actively implementing the actual Ashtadhyayi declension rules.
- **Real sandhi segmentation.** Word boundaries here are whitespace.
  [`vidyut-cheda`](https://github.com/ambuda-org/vidyut) or
  [`kmadathil/sanskrit_parser`](https://github.com/kmadathil/sanskrit_parser)'s
  dynamic-programming sandhi-split search are the right components to bind
  to for real text.
- **Fully automatic rule-conflict resolution.** `SubsumptionEngine` derives
  specificity from each rule's *declared* condition set and correctly
  refuses to guess on genuine ambiguity — but those condition sets are
  still hand-written, not extracted automatically from arbitrary rule
  logic. See `docs/DESIGN.md` / `docs/position-paper.md` §6.
- **Control flow.** This is a declarative/relational layer (facts + rules,
  like Prolog), not a general-purpose imperative or functional language.
  Kāraka roles have nothing to say about loops or mutation.

## Status

Proof-of-concept. 14/14 tests passing. Two of the four original limitations
(fixed arity ceiling, non-composable manual rule priority) have been
addressed per reviewer feedback — see `docs/position-paper.md` §6 for what
that resolution does and doesn't cover. Not yet published to arXiv or PyPI.

## License

MIT — see [`LICENSE`](LICENSE).
