# Kāraka-Calling-Convention (KCC): a Pāṇinian logic language

A design sketch and working proof-of-concept, not a claim of a finished language.

## 1. Thesis (narrow, defensible)

Not "Sanskrit is a superior programming language." That claim is well-worn and
hard to defend — see the persistent (and exaggerated) "NASA said Sanskrit is
the only unambiguous language for AI" myth that trails any discussion of this
topic. The actual 1985 Briggs paper it descends from makes a much narrower
claim: that Pāṇinian **kāraka** (semantic case-role) analysis produces
structures equivalent to AI semantic nets, and that Sanskrit's case-marking
makes word order largely irrelevant to meaning.

The defensible thesis: **Sanskrit's kāraka system is a better-tested design
for a role-based (rather than positional) argument-binding convention than
anything mainstream languages currently use**, and this maps unusually well
onto logic/relational programming, where positional argument binding
(Prolog's arity- and mode-dependent unification) is a known, long-standing
usability problem.

## 2. What's genuinely reusable, and what isn't

| Sanskrit feature | Reusable as | Caveat |
|---|---|---|
| Kāraka roles (agent/object/instrument/recipient/source/locus) | Order-independent argument binding for predicates/functions | Only 6-7 roles; doesn't generalize to arbitrary-arity APIs without a fallback (see §4) |
| Vibhakti (case suffixes) | Surface syntax marking roles on tokens | Real declension is stem/gender-dependent — don't reinvent; bind to `vidyut-prakriya` |
| Pāṇini's rule-ordering (utsarga/apavada) | Priority-based rewrite/macro system | Automatic rule-conflict resolution is an **open problem** even in the best existing Ashtadhyayi implementations (see §3) — plan on manual/explicit priority, not automatic derivation |
| Sandhi (phonological merge at word boundaries) | Token normalization pass | In practice a **combinatorial segmentation search problem**, not a free syntactic win — treat as a lexer stage with real cost, not magic |
| Samāsa (compounding) | Nested/composable naming, product vs. attribute-access semantics | Compound-type ambiguity (tatpuruṣa vs. bahuvrīhi) is itself a disambiguation problem in real Sanskrit texts |
| Free word order | — | This is a *human* usability property of a spoken/written language. For a programming language, order-independence is worth keeping (it's the point), but "free" isn't free — it has to be enforced by unambiguous role-marking, or you've just made the parser's job harder for no compiler-side benefit |

## 3. Prior art (so this doesn't reinvent things that already exist)

- **[vidyut](https://github.com/ambuda-org/vidyut)** (Ambuda project, Rust + Python bindings) —
  segmentation, sandhi utilities, and `vidyut-prakriya`, an in-progress full
  implementation of Ashtadhyayi word derivation. **This is the dependency to
  bind to for real morphology**, not something to reimplement.
- **Gérard Huet's Sanskrit Heritage Engine** — the original computational
  Pāṇinian grammar model for parsing/generation; foundational reference for
  sandhi and segmentation algorithms.
- **kmadathil/sanskrit_parser** — dynamic-programming sandhi-split search
  producing a DAG of valid segmentations, then projective dependency parsing
  of that DAG into kāraka relations. Closest existing thing to "parse real
  text into kāraka frames"; explicitly still under active development, with
  known over- and under-generation issues.
- **"Implementing Pāṇini's Grammar"** (Language Log, 2023) — ~2,000 of the
  ~4,000 Ashtadhyayi rules implemented in Rust/WASM for word generation. The
  author is explicit that automatic rule-ordering resolution was **not**
  solved — rules were manually ordered to produce valid output. Treat this as
  the current honest state of the art on that specific sub-problem.
- **Cosmetic "Sanskrit programming languages"** (several small GitHub/bison-yacc
  projects) — keyword-translation only, C-like positional syntax underneath.
  Useful as a list of "don't just do this."

No existing project does kāraka-role argument binding as a **calling
convention** for a general-purpose or logic language. That's the actual gap.

## 4. Architecture

```
surface text
     |
     v
[1] Lexer / segmenter        -- real version: bind to vidyut-cheda for
                                 sandhi-aware word segmentation
     |
     v
[2] Kāraka resolver           -- toy version: suffix table (this repo)
                                 real version: vidyut-prakriya morphological
                                 tags -> role mapping
     |
     v
[3] Frame (the AST)           -- verb + {role: argument} dict
                                 == a small labeled-edge graph around one
                                 event node. This is not a coincidence: it's
                                 why kāraka frames compile so naturally to
                                 both Prolog facts and property-graph writes.
     |
     v
[4] Sūtra rewrite engine      -- ordered, priority-resolved rewrite rules
                                 (utsarga/apavada), applied to Frames
     |
     v
[5] Codegen                   -- Prolog clauses / Cypher (FalkorDB) / a
                                 small stack VM, pick per use case
```

### On arity beyond the 6 kāraka roles
Real predicates often need more than 6 argument slots. Two honest options,
neither original to Sanskrit: (a) allow the genitive/sambandha role to carry
a nested sub-frame (attribute chains), or (b) fall back to named tags for
anything that isn't one of the six classical roles, same as keyword
arguments in Python today. Don't force everything into kāraka roles just
because it's thematically clean — that's the same mistake as the cosmetic
keyword-translation projects, just one level deeper.

## 5. Worked example (this repo, `karaka_lang/` package + `examples/`)

Three word orders of "the robot goes to the kitchen" parse to an identical
`Frame` object (`examples/robot_kitchen.py`) — the calling convention is
genuinely order-free, verified by an assertion, not just claimed, and
covered by `tests/test_parser.py::test_order_invariance`.

A Rylands v. Fletcher–shaped statement ("the man causes harm to the field by
means of the flood from the reservoir") is parsed into a frame with
`karta` (agent), `sampradana` (recipient/harmed party), `karana`
(instrument), and `apadana` (source) roles bound simultaneously — which is
close to the six-cases-across-three-jurisdictions structure already being
used in the `falkor-irac` Rylands experiment design, for what it's worth as
a sanity check that the roles map onto real legal-relation structure and not
just toy examples.

A small Sūtra engine (`karaka_lang/sutra.py`) then demonstrates
utsarga/apavada resolution in `examples/rylands_fletcher.py`: a general
"strict liability" rule fires first, then a more specific
"instrument-based liability" rule overrides it — implemented as an explicit
priority number, not automatic derivation (per the caveat in §3).

Frames compile to both a Prolog fact set and a Cypher `MERGE` graph write
from the same source object (`karaka_lang/codegen.py`), since a
role-labeled frame already is a small labeled-edge structure.

## 6. Roadmap if someone wanted to take this further

1. **Replace the toy suffix table with real morphology.** Bind to
   `vidyut-prakriya` for declension-correct case marking (stem class,
   gender, number all affect the actual suffix) instead of the fixed
   a-stem-masculine table used here.
2. **Replace the toy tokenizer with real segmentation.** Bind to
   `vidyut-cheda` or `kmadathil/sanskrit_parser`'s DP sandhi-split search,
   since word boundaries in real (or even just realistically-styled) text
   aren't whitespace-delimited.
3. **Formalize the Sūtra engine's conflict resolution**, ideally as a
   partial order over rule specificity (some rules are incomparable, not
   just linearly ranked) — this is the actual open research problem flagged
   in §3, and solving it properly would be a genuine contribution rather
   than a restatement.
4. **Pick one codegen target and make it real.** The Prolog/Cypher dual
   output here is illustrative; a real system should probably commit to one
   (Cypher/FalkorDB is the more natural fit given the graph-native semantics
   of a Frame) and build proper query/execution semantics on top, not just
   fact assertion.
5. **Decide what "control flow" means.** This sketch is purely
   declarative/relational (facts and rules, like Prolog). A general-purpose
   imperative or functional layer on top would need its own design — kāraka
   roles have nothing to say about loops, mutation, or continuations, and
   claiming otherwise would be overreach.

## 7. What this is *not* claiming

- Not claiming this is faster, safer, or more "AI-native" than existing
  logic languages in any measured sense — no benchmarks exist yet, and
  "AI-native" claims in particular tend to be asserted rather than
  demonstrated across current commentary on this topic.
- Not claiming free word order is a parsing advantage in general — it's a
  deliberate trade (role-marking cost for order-independence benefit), worth
  it specifically where argument-role clarity matters more than terseness
  (e.g., multi-party legal relations, API calls with many optional params),
  not obviously worth it everywhere.
- Not claiming to have solved Pāṇinian rule-ordering — explicitly punting to
  manual priority numbers, same as the most honest existing implementation.
