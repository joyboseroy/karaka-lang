# The Kāraka Calling Convention: Semantic-Role Argument Binding for Logic Programming

**Position paper / work-in-progress report.**
Category: cs.PL (Programming Languages), cross-list cs.AI, cs.CL

## Abstract

Positional argument binding — `f(x, y, z)` assigning meaning by slot
order — degrades as arity grows, and logic programming suffers it worst:
each position's semantics must be remembered rather than read off the
call site, and keyword arguments only trade this for a vocabulary that is
local to each predicate.

We present the *Kāraka Calling Convention* (KCC): arguments are bound by
a fixed vocabulary of six semantic roles (agent, object, instrument,
recipient, source, locus), drawn from Pāṇinian Sanskrit grammar and
carried morphologically by each argument. Because the vocabulary is
predicate-independent, a rewrite rule written once against a role applies
across all predicates — the property keyword arguments and PropBank
framesets lack. A parsed statement is already a labeled-edge graph, so
the same object compiles to Prolog facts and to property-graph writes
with no lowering pass, and groundness alone decides whether a statement
is an assertion or a query. Rule conflicts resolve by requirement-set
subsumption (the Pāṇinian utsarga/apavada discipline), with incomparable
rules rejected at registration as ambiguous.

We give a formal definition, a worked end-to-end example, and a tested
reference implementation with optional real Aṣṭādhyāyī morphology via
vidyut-prakriya; a prior-art search found one contemporaneous system
using kāraka roles as call-site labels, and we characterize the overlap
from its source. Measured readability benefit is open work, stated as
such.

## 1. Introduction

The idea that Sanskrit's grammar has something to offer computer science is
not new. Briggs (1985) argued in *AI Magazine* that Pāṇinian *kāraka*
analysis — a system of six semantic case roles attached to nouns via case
endings — produces structures functionally equivalent to the semantic nets
then used in AI knowledge representation, and that because Sanskrit word
order carries little more than stylistic weight, kāraka-marked sentences
are naturally suited to a syntax-free representation: a flat list of
role-tagged semantic relations.

Most subsequent "Sanskrit programming language" projects have taken a
different and much shallower approach: translating a conventional language's
keywords into transliterated Sanskrit while leaving positional, C-like
syntax untouched. This addresses none of the structural claims in Briggs's
argument and is, in effect, orthographic rather than architectural.

This paper takes the architectural claim seriously and narrowly: kāraka
roles as a calling convention for logic/relational programming, where the
positional-argument problem is sharpest. Pāṇini supplies the role
vocabulary and the rule-ordering discipline; he is not a source of
validity for the claim itself. The observation everything else in this
paper follows from is structural: a statement whose arguments carry their
own roles is already a labeled-edge graph, and a representation that is
already a graph needs no lowering pass to become either a fact base or a
query.

## 2. Related work

**Linguistic case grammar.** Fillmore's case grammar (1968) independently
proposes a small universal set of semantic roles (agent, instrument,
objective, etc.) governing verb argument structure, largely converging with
the kāraka system despite arising from a different linguistic tradition.
Kāraka theory predates it by roughly two millennia and comes with a far
more extensively worked-out formal apparatus (Pāṇini's *Aṣṭādhyāyī*, c.
4th century BCE), which is the reason we work from the Sanskrit tradition
rather than Fillmore's.

**Abstract Meaning Representation and PropBank.** AMR (Banarescu et al.,
2013) represents sentence meaning as a rooted, directed acyclic graph whose
edges are labeled with roles drawn from PropBank framesets — numbered
arguments `:ARG0`–`:ARG5` rather than named ones. This is the closest
existing large-scale system to what a KCC `Frame` is: a role-labeled graph
around an event/predicate node. The load-bearing difference is that
PropBank's numbered roles are *predicate-specific*: `:ARG0` is glossed as
"wanter" for the frameset `want-01`, "sleeper" for `sleep-01`, and
"creator" for `develop-02` — each verb sense defines its own local mapping
from argument number to meaning, recorded in a separate frameset table. A
kāraka role is not relative to the predicate in this way: *karta* means
"agent" for every verb, uniformly, by construction, because the role
vocabulary is fixed by the grammar rather than declared per-predicate. This
is the precise sense in which KCC's roles are "grammar-level" rather than
merely named-argument-level, and it is what makes generic, predicate-agnostic
rules possible in §4 (a rule can match "any frame with a *karana*,
regardless of verb," which is not expressible against ARG0–ARG5 without
first resolving each verb's frameset).

**Frame semantics and knowledge representation.** Minsky's frame systems
(1974) and Fillmore's later frame semantics (1976) both use "frame" for a
structured slot-and-filler representation of a stereotyped situation,
independently of the AMR/PropBank tradition above; our use of `Frame` for
a verb-plus-roles structure is consistent with this older sense, though we
did not set out to implement either directly.

**Datalog and RDF.** A KCC `Frame`, compiled to normalized binary
predicates (§3, §5), is structurally a small Datalog fact base, and
compiled to Cypher it is structurally an RDF-like labeled-edge graph (a
kāraka role plays the part of an RDF predicate/property). The novelty
claimed here is not the target representation — both are well established
— but the *source* representation and the argument-binding discipline that
produces it, which neither Datalog nor RDF specify on their own: both are
downstream data models, agnostic to how the roles attached to a given
predicate were decided or named in the first place.

**Computational Sanskrit infrastructure.** Huet's Sanskrit Heritage
Engine, the `vidyut` toolkit (whose `vidyut-prakriya` this implementation
binds to, §5), and `kmadathil/sanskrit_parser` (DP sandhi-split search
into kāraka dependency graphs) are the serious computational-Sanskrit
substrate; none is a programming language. A partial Rust implementation
of the Aṣṭādhyāyī ("Implementing Pāṇini's Grammar," Language Log, 2023)
documents that automatic rule-ordering remains unsolved there — rules
were manually ordered — which calibrates what §4 does and does not claim.

**Programming languages.** Keyword arguments (Python, Common Lisp),
named-field structs (Rust), and named-parameter libraries for positional
languages (e.g. Boost.Parameter for C++) are the closest mainstream
analogues to role-based binding, but each function or struct declares its
own local keyword vocabulary — `host=`, `timeout=`, `retries=` — rather
than drawing from a small, fixed, predicate-independent set. That
local-vocabulary property is exactly what §3.1 argues is the substantive
difference from kāraka roles, not merely a stylistic one. Prolog
predicates remain purely positional, which is the specific gap this paper
targets.

**Specificity-ordered rule systems.** The subsumption-ordered rewrite
engine of §4 has direct precedent in two literatures we did not originate.
Predicate dispatch (Ernst, Kaplan & Chambers, 1998) generalizes OO method
dispatch to arbitrary predicates over arguments and resolves overriding by
logical implication between method predicates — structurally the same
move as ordering sutras by requirement-set inclusion, and their
compile-time ambiguity detection for non-comparable methods anticipates
our `AmbiguityError`. Separately, prioritized-conflict handling in
non-monotonic logic programming — courteous logic programs (Grosof, 1997)
and defeasible logic programming (García & Simari, 2004) — formalizes
general-rule/exception override for rule bases at large. The
utsarga/apavada discipline is thus best understood as a very early
instance of a now well-studied pattern; what this paper adds is not the
pattern but its coupling to a fixed semantic-role vocabulary, which is
what lets the rules be predicate-agnostic (§3.1).

**Closest prior art: Prakash's Karaka language.** After an earlier draft
claimed this niche was unoccupied, a prior-art search found Karaka
(Prakash, 2026), published to the Rust crates registry in June 2026: a
Devanagari-first imperative language in which the six kāraka roles form a
fixed vocabulary for declaring function parameters and labeling call-site
arguments (`कर्ता: <value>`), alongside user-defined labels. We verified
this from the published source rather than secondhand description. Two
independent implementations within months of each other is better read as
evidence the idea is timely than as a priority dispute. The verified
differences:

| | Prakash's Karaka (2026) | This work (KCC) |
|---|---|---|
| Role binding | explicit call-site labels | morphological (case ending on the token) |
| Paradigm | imperative / OO, interpreter | declarative / relational |
| Compilation | none (tree-walking) | Prolog facts + Cypher graph writes |
| Rewrite layer | none | subsumption-ordered, ambiguity-rejecting |
| Query duality | none | groundness decides assertion vs. query |

The shared element — the six-role vocabulary — is therefore no longer
uniquely ours; the composition in the right-hand column is what this
paper claims (§8).

**Sanskrit-based programming language specifications.** Khanganba & Jha
(2020) specify "Sanskritam," a controlled-natural-language programming
syntax in which Sanskrit case morphology carries program semantics — the
genitive marks assignment (per the Pāṇinian metarule *ṣaṣṭhī
sthāneyogā*), the locative marks scope headers and conditions, mirroring
the Aṣṭādhyāyī's own adhikāra convention. Kārakas are not a calling
convention there, but it is the closest academic precedent for case
morphology carrying programming-language semantics.

No existing system we could find combines morphologically-marked kāraka
binding, dual compilation to logic facts and property-graph writes,
subsumption-derived rule ordering, and an assertion/query duality — a
claim now made with the humility of having had its broader predecessor
falsified. The components have the precedents named above; the
composition is what we claim.

## 3. Design: the Kāraka Calling Convention

(Convention: prose uses IAST diacritics — kāraka, Pāṇini, Aṣṭādhyāyī —
while code identifiers use their ASCII forms — `karta`, `karana` — since
the implementation is ASCII-native.)

A KCC statement consists of one verb (predicate) and up to six role-marked
arguments — *karta* (agent), *karma* (object), *karana* (instrument),
*sampradana* (recipient), *apadana* (source), *adhikarana* (locus) — plus
an overflow *sambandha* (genitive/possessive) role for nested sub-frames.
Each argument's role is determined by a marker carried on the token itself
(in the reference implementation, a suffix), not by its position in the
statement. The parse target is a `Frame`: a verb plus a `{role: argument}`
mapping. Three permutations of the same statement's word order produce an
identical `Frame` by construction (verified by test, §5).

Arity beyond the six classical roles does not require adding more roles:
any role's value can itself be a nested `Frame` rather than a leaf string,
so a single "instrument" can expand into an entire sub-event with its own
roles (e.g. an instrument that is itself caused by a prior event). This
generalizes cleanly to arbitrary nesting depth, though it does mean deeply
nested KCC statements trade the flat readability of a two- or three-role
frame for the structure of a small tree — a real trade, not a free win.

A `Frame` is, incidentally, already a small labeled-edge graph structure
(event node, role-labeled edges to argument nodes), which motivates the two
compilation targets evaluated here: normalized Prolog facts (one binary
predicate per role, avoiding positional-term degradation) and Cypher
`MERGE` statements against a property graph (e.g. FalkorDB). Why this
matters, rather than being a curiosity: it collapses the usual distance
between a program and a knowledge base. In a conventional stack, getting
from source code to something a graph database or reasoner can consume
requires an extraction pipeline — parse, walk the AST, decide on a schema,
emit triples. Here there is nothing to extract: the parsed statement is
the graph, so a KCC program is simultaneously executable (as facts and
queries), storable (as a property graph), and pattern-matchable (by any
graph or Datalog engine) with no representation change at any step. Both
codegen paths recurse through nested frames, emitting a fresh sub-event
identifier and linking it from the parent by the role name — a
Skolemization step, in the standard logic-programming sense: an
existentially-quantified sub-event ("there exists some flooding event that
is the instrument here") is witnessed by a fresh constant, which is
exactly what turns a nested, tree-shaped `Frame` into flat, indexable
relational tuples without losing the parent-child relationship.

### 3.1 Why this is not just keyword arguments with extra steps

Keyword arguments already give order-independence and readable call
sites. The difference is a single property, stated first and defended
after:

> **Proposition (predicate-independence).** A role vocabulary is
> *predicate-independent* iff the interpretation of a role does not
> depend on which predicate it is attached to. A rewrite rule is
> *predicate-agnostic* iff its applicability is decidable from
> `facts(F)` alone, with no per-predicate lookup. A fixed,
> predicate-independent vocabulary is what makes predicate-agnostic
> rules well-defined.

Python keyword names, Rust named fields, and PropBank's `:ARG0`–`:ARG5`
(the largest deployed role-labeling system, underlying AMR) are all
*predicate-relative*: PropBank's own framesets gloss `:ARG0` as "wanter"
under `want-01`, "sleeper" under `sleep-01`, and "creator" under
`develop-02` — the same label, three meanings, resolved only through a
per-verb table. A kāraka role carries no such indirection: *karta* means
agent for every predicate, by construction.

The consequence is demonstrable, not aesthetic. The following rule names
no verb:

```python
SubsumptionSutra(
    name="mediated-transfer-classification",
    requires=frozenset({"has:karana", "has:sampradana"}),
    transform=lambda f: Frame(f.verb, {**f.roles, "class": "mediated-transfer"}))
```

Applied to two frames under *different* verbs — `hara` (causes harm) and
`dada` (gives) — it classifies both, and leaves a two-role motion frame
untouched (output generated by the test suite, `test_predicate_agnostic_
rule_applies_across_different_verbs`):

```
Frame(hara, class=mediated-transfer, karana=jal, karta=man, sampradana=ksetr)
Frame(dada, class=mediated-transfer, karana=dhan, karta=nar, sampradana=putr)
```

Written against keyword arguments or ARG-numbered roles, this requires
either one clause per predicate or a maintained mapping from each local
vocabulary to a shared one — and that mapping *is* a kāraka layer,
reinvented.

Two honest qualifications. First, the vocabulary property alone is
replicable anywhere: globally reserving `agent`, `instrument`,
`recipient` as keyword names in any language reproduces it, and Prakash's
Karaka (§2) does essentially this with the Sanskrit terms. The vocabulary
is therefore necessary for this paper's contribution but not sufficient;
the contribution is the composition (§8). Second, real Sanskrit
complicates the surface mapping: passivization and idiosyncratic case
government mean the vibhakti-to-kāraka correspondence is itself
verb-conditioned in general (§6). That table, if added, is structurally a
frameset — but it sits at the *surface* layer only. Its output is still
the fixed six-role vocabulary, so every rule downstream of parsing
remains predicate-agnostic; what becomes verb-conditioned is the mapping
from case ending to role, not the meaning of the role.

### 3.2 Formal definition

The core structure is small enough to state completely:

```
Frame    ::=  (Verb, Bindings)
Bindings ::=  Role ⇀ Value            (a partial map; each role at most once)
Role     ∈    {karta, karma, karana, sampradana, apadana, adhikarana, sambandha}
Value    ::=  Atom | Var | Frame
Var      ::=  "?" Atom
```

A frame is *ground* if no `Var` occurs in it (recursively); ground frames
denote assertions, non-ground frames denote queries (§3.3). The fact set
of a frame, used by the rule engine (§4), is defined recursively:

```
facts(F) = {verb=v}  ∪  {has:r | r ∈ dom(F.bindings)}
           ∪  { r.φ | r ↦ F' ∈ F.bindings, F' a Frame, φ ∈ facts(F') }
```

Here `verb=v` records the frame's predicate, `has:r` records that role
`r` is bound, and `r.φ` prefixes every fact `φ` of a nested sub-frame
with the role it hangs under. So for a harm event whose instrument is
itself a rainfall event, `facts` contains `verb=hara`, `has:karta`,
`has:karana`, and the nested `karana.verb=varsa`, `karana.has:karta` —
which is what lets a rule condition on "the instrument was a natural
event." A rule's condition language is deliberately minimal: `requires`
is a conjunction of these atomic facts, with no negation or disjunction;
subsumption between rules is then plain set inclusion, which is what
keeps the ordering of §4 decidable at rule-registration time.

### 3.3 A worked example, end to end

The reviews of earlier drafts converged on one request: show the pipeline
once, completely. The statement is a Rylands v. Fletcher-shaped tort
relation — "the man causes harm to the field by means of the flood, from
the reservoir":

```
manah ksetraya jalena jalasayat harati
```

Each token carries its role as a case suffix (`-ah` agent, `-aya`
recipient, `-ena` instrument, `-at` source; `-ti` marks the verb), so the
parser needs no positional information and any permutation of the five
words parses identically:

```python
>>> from karaka_lang import parse
>>> parse("manah ksetraya jalena jalasayat harati")
Frame(hara, apadana=jalasay, karana=jal, karta=man, sampradana=ksetr)
```

Two rules are then applied. In the implementation, a rule is a declared
requirement set plus a transform:

```python
SubsumptionSutra(
    name="default-liability",                     # utsarga: the general rule
    requires=frozenset({"verb=hara"}),
    transform=lambda f: Frame(f.verb, {**f.roles, "liability": "strict"}))

SubsumptionSutra(
    name="instrument-liability-exception",        # apavada: the exception
    requires=frozenset({"verb=hara", "has:karana"}),
    transform=lambda f: Frame(f.verb, {**f.roles, "liability": "instrument-based"}))
```

The second rule's requirements strictly include the first's, so it is more
specific and applies last, overriding on the shared output key. Had the two
requirement sets been incomparable, the engine would raise `AmbiguityError`
instead of choosing. The resolved frame then compiles, without an
intermediate lowering pass, to both targets:

```prolog
% to_prolog(frame): one binary predicate per role, arity never grows
event(e1, hara).
apadana(e1, jalasay).
karana(e1, jal).
karta(e1, man).
liability(e1, instrument-based).
sampradana(e1, ksetr).
```

```cypher
// to_cypher(frame): the same shape as labeled edges
MERGE (e:Event {verb: "hara"})
MERGE (n_jalasay:Entity {name: "jalasay"}) MERGE (e)-[:APADANA]->(n_jalasay)
MERGE (n_jal:Entity {name: "jal"})         MERGE (e)-[:KARANA]->(n_jal)
MERGE (n_man:Entity {name: "man"})         MERGE (e)-[:KARTA]->(n_man)
MERGE (n_ksetr:Entity {name: "ksetr"})     MERGE (e)-[:SAMPRADANA]->(n_ksetr)
```

Finally, replacing any constant with a variable turns the same structure
into a question. "*Who* causes harm by means of the flood?" is the same
frame with `karta` left open, and it compiles to a query rather than a
write:

```python
>>> compile_frame(parse("?kah jalena harati"), target="prolog")
event(E, hara), karana(E, jal), karta(E, K).

>>> compile_frame(parse("?kah jalena harati"), target="cypher")
MATCH (e:Event {verb: "hara"})
MATCH (e)-[:KARANA]->(:Entity {name: "jal"})
MATCH (e)-[:KARTA]->(k:Entity)
RETURN k.name
```

Assertion and query are one type; groundness decides which you get. All
output above is generated by the reference implementation, not typeset by
hand.

## 4. Rule resolution: from manual priority to subsumption-derived order

Pāṇini's grammar is organized around general rules (*utsarga*) that can be
overridden by more specific exception rules (*apavada*) — the same
principle underlying CSS specificity or pattern-match ordering in
functional languages. An initial implementation used an explicit,
author-assigned integer priority per rule. Two independent reviewers of an
earlier draft of this paper flagged the same weakness: manual integers
don't compose — if two independently authored rule sets each assign
`priority=5`, combining them produces an arbitrary ordering rather than a
meaningful one.

The current implementation instead derives specificity from **condition
subsumption**. Each rule declares a set of required conditions on the frame
(e.g. `{verb=hara, has:karana}`); rule A is apavada to rule B iff A's
requirements are a strict superset of B's, and applies later, overriding
B on any conflicting output. Requirement-set inclusion induces a partial
order over applicable rules. If two applicable rules are
incomparable under this order — neither a subset of the other — the engine
raises a structural `AmbiguityError` rather than guessing, mirroring the
way Pāṇinian commentators required an explicit tie-breaking rule when a
conflict didn't resolve by the grammar's own ordering principles. This is
deliberately stricter than common practice — many rule systems default to
"last defined wins" or fall back to declaration order — and a
configurable tie-breaker would be easy to add; we chose rejection as the
default because silent, order-dependent resolution is precisely the
composability failure the manual-priority version suffered from. This
closes the composability gap the reviewers identified, though it is worth
noting plainly that the "requirements" a rule declares are still
author-written, not automatically extracted from the `condition` predicate
itself — full automatic subsumption analysis over arbitrary Python
predicates is not attempted, and would be a substantially larger undertaking.

## 5. Implementation and evaluation

The reference implementation (`karaka_lang`, Python) consists of a
tokenizer/role-resolver, the `Frame` AST, two rewrite engines (§4),
codegen to Prolog and Cypher in both assertion and query mode (§3.3), and
an optional morphology module binding to `vidyut-prakriya` that replaces
the toy suffix table with actual Aṣṭādhyāyī derivation over a registered
lexicon — every analyzed form carries the sutra numbers that derived it
(e.g. `aSvena` resolves to `aSva` + instrumental → *karana* via the chain
1.2.45 → 4.1.2 → ... → 8.4.68). A 23-test suite covers: order invariance
across permutations; duplicate-role and missing-verb error handling; the
five-role tort relation of §3.3; utsarga/apavada override under both
engines, with and without a matching exception; rejection of incomparable
rules via `AmbiguityError`; a predicate-agnostic rule applying across
different verbs (§3.1); rules conditioning on nested sub-event facts;
nested-`Frame` arity extension with recursive codegen; query-mode
compilation to both targets; and, when vidyut is installed, real-declension
round-trips including rejection of out-of-lexicon and ambiguous forms. All
23 tests pass (20 without vidyut; the morphology tests skip cleanly). This
remains a proof-of-concept evaluation, not a benchmark — no comparison
against Prolog predicate readability or programmer performance has been
conducted (§6).

## 6. Limitations

We list these explicitly rather than in passing, since they bound the
paper's actual claim:

- **Morphology — partially addressed.** The optional vidyut-prakriya
  binding (§5) performs real Aṣṭādhyāyī derivation, but over a closed,
  registered lexicon (analysis-by-generation), singular forms only, and
  with the default vibhakti-to-kāraka correspondence. Real Sanskrit breaks
  that neat mapping under passivization and verbs governing idiosyncratic
  cases; a per-verb mapping table is the known fix and is future work. The
  zero-dependency toy suffix table remains the fallback.
- **Whitespace tokenization.** Real Sanskrit sandhi merges word boundaries;
  the reference implementation sidesteps this entirely. `vidyut-cheda` or
  `kmadathil/sanskrit_parser`'s DP sandhi-split search are the correct
  components to integrate, and neither is trivial (both report ongoing
  over/under-generation issues). This remains fully open.
- **Arity ceiling — partially addressed.** Nested `Frame`s under a role
  remove the hard six-role ceiling (§3), but the current subsumption engine
  (§4) only inspects the *top-level* frame's facts when checking rule
  applicability and ambiguity — it does not yet recurse into nested
  sub-frames when computing the fact set a rule's `requires` is checked
  against. A rule that needs to condition on a property of a nested
  sub-event isn't yet expressible. This is a smaller, more tractable gap
  than the original "six roles only" problem, but it is a real one.
- **Rule-conflict resolution — partially addressed.** Specificity is now
  *derived* from declared condition sets rather than an author-assigned
  integer (§4), and genuinely incomparable rules raise `AmbiguityError`
  rather than resolving silently. This directly answers the composability
  objection raised by reviewers. It does not, however, extract those
  condition sets automatically from arbitrary rule logic — a rule's
  `requires` is still hand-declared by whoever writes the rule, and could
  in principle be declared inconsistently with what its `condition`
  function actually checks. Automatic extraction of `requires` from
  unrestricted host-language predicates is out of scope (and undecidable
  in general, by Rice's theorem); a constrained rule-condition DSL would
  make it tractable, at the cost of expressiveness.
- **No human-subject or performance evaluation.** All claims about
  readability improvements over positional Prolog predicates are argued,
  not measured.
- **No claim of general-purpose applicability.** Kāraka roles say nothing
  about control flow, mutation, or concurrency; this is a
  declarative/relational calling convention, not a general-purpose language
  design.

## 7. Future work

**Open research questions**, in the order we consider most consequential:
(1) *Does the readability benefit exist and how large is it?* A
matched-arity comparison of KCC-normalized facts against positional Prolog
predicates, measuring comprehension time and error rate across
participants, is the single piece of evidence this paper most lacks; the
paired materials can be prepared in advance in the repository. (2) *What
is the right verb-conditioned role mapping?* The default vibhakti-kāraka
correspondence breaks under passivization and idiosyncratic case
government; a per-verb mapping table is structurally identical to a
PropBank frameset, which raises the genuinely open question of how much
predicate-independence survives contact with real verb semantics. (3)
*What are query-mode semantics over nested frames?* Variables inside
sub-events, and quantification across nesting levels, are unspecified
beyond one level.

**Engineering completion tasks**, more mechanical than open: executing
generated Cypher against a live graph store rather than emitting text;
sandhi-aware input via `vidyut-cheda`, with the honest complication that
segmentation is ambiguous and the parser must surface candidate sets;
dual/plural number; and LaTeX conversion for submission.

## 8. Conclusion

The contribution is a composition, stated after a prior-art search
falsified an earlier, broader claim: morphologically-marked kāraka role
binding, direct compilation of role-labeled statements to both
logic-programming facts and property-graph writes, subsumption-derived
rule ordering with compile-time ambiguity rejection, and an
assertion/query duality decided by groundness — restricted to
declarative/relational programming. The individual components have
precedents, now cited; the six-role vocabulary itself appears
independently in a contemporaneous system, which we read as evidence of
timeliness. The proof-of-concept demonstrates order invariance holds by
construction and that the representation compiles to both targets without
a lowering pass. Whether the composition yields a measurable readability
or maintainability improvement over keyword-argument and named-struct
conventions remains the open question this paper explicitly does not
settle.

## References

- Briggs, R. (1985). Knowledge Representation in Sanskrit and Artificial
  Intelligence. *AI Magazine*, 6(1), 32–39.
- Ernst, M. D., Kaplan, C., & Chambers, C. (1998). Predicate Dispatching:
  A Unified Theory of Dispatch. *Proceedings of ECOOP '98*.
- Fillmore, C. J. (1968). The Case for Case. In *Universals in Linguistic
  Theory*, Holt, Rinehart and Winston.
- Fillmore, C. J. (1976). Frame Semantics and the Nature of Language.
  *Annals of the New York Academy of Sciences*, 280(1), 20–32.
- García, A. J., & Simari, G. R. (2004). Defeasible Logic Programming: An
  Argumentative Approach. *Theory and Practice of Logic Programming*,
  4(1-2), 95–138.
- Grosof, B. N. (1997). Prioritized Conflict Handling for Logic Programs.
  *Proceedings of the International Logic Programming Symposium*.
- Khanganba, K. K., & Jha, G. N. (2020). Formal Sanskrit Syntax: A
  Specification for Programming Language. *Proceedings of AACL-IJCNLP
  2020 Student Research Workshop*, 72–78.
- Minsky, M. (1974). A Framework for Representing Knowledge. MIT-AI
  Laboratory Memo 306.
- Banarescu, L. et al. (2013). Abstract Meaning Representation for
  Sembanking. *Proceedings of the 7th Linguistic Annotation Workshop and
  Interoperability with Discourse*.
- Kingsbury, P. & Palmer, M. (2002). From Treebank to PropBank.
  *Proceedings of LREC*.
- Prakash, S. (2026). Karaka: a Devanagari-first programming language.
  `karaka-core` 0.1.0, Rust crates registry, June 2026.
  https://crates.io/crates/karaka-core
- Huet, G. Sanskrit Heritage Engine.
- Ambuda Project. `vidyut`: segmentation, sandhi, and Aṣṭādhyāyī-based
  word derivation. https://github.com/ambuda-org/vidyut
- Madathil, K. et al. `sanskrit_parser`.
  https://github.com/kmadathil/sanskrit_parser
- "Implementing Pāṇini's Grammar." Language Log, 2023.
  https://languagelog.ldc.upenn.edu/nll/?p=61507
