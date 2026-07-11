# The Kāraka Calling Convention: Semantic-Role Argument Binding for Logic Programming, via Pāṇinian Grammar

**Position paper / work-in-progress report.**
Category: cs.PL (Programming Languages), cross-list cs.AI, cs.CL

## Abstract

Positional argument binding — the convention by which `f(x, y, z)` assigns
meaning to `x`, `y`, `z` purely by their slot order — is a load-bearing
assumption in most programming languages, and it degrades predictably as
arity grows: Prolog predicates in particular become unreadable past four or
five arguments, since the meaning of each position must be memorized rather
than read off the call site. We contribute a role-based calling convention,
the *Kāraka Calling Convention* (KCC), whose semantics happen to coincide
with the six-role *kāraka* system of Pāṇinian Sanskrit grammar (agent,
object, instrument, recipient, source, locus) — Pāṇini is the inspiration
for the role vocabulary and the rule-ordering discipline, not a source of
validity for the claim itself. The central structural fact is that a
parsed statement — verb plus role-labeled arguments — is already a small
labeled-edge graph, not merely an AST: the same object compiles directly to
normalized relational facts and to property-graph writes with no
intermediate lowering pass. Because each argument carries its own role
marker, argument order is irrelevant to meaning; arity beyond six roles is
handled by letting any role point to a nested sub-relation instead of a
leaf value; and rule-conflict resolution, modeled on the Pāṇinian
utsarga/apavada (general-rule/exception) principle, is derived from
condition subsumption rather than an author-assigned priority number, with
a structural ambiguity error raised rather than a silent guess when two
rules' conditions are incomparable. We restrict this work to declarative,
relational programming, where the positional-argument problem is sharpest
and best documented; we describe the design and a working implementation
with a passing test suite, and treat real Sanskrit morphology and any
measured (rather than argued) readability benefit as open work.

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

This paper reports on an attempt to take the architectural claim seriously
and narrowly: **can kāraka roles function as a calling convention**,
independent of any claim about Sanskrit as a human-facing surface syntax?
We restrict scope deliberately to logic/relational programming, where the
positional-argument problem is sharpest and best documented, rather than
claiming applicability to general-purpose or imperative languages.

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

**Computational Sanskrit infrastructure.** The Sanskrit Heritage Engine
(Huet) provides a computational model of Pāṇinian grammar for parsing and
generation. `vidyut` (Ambuda project) provides segmentation, sandhi
utilities, and an in-progress full implementation of Ashtadhyayi word
derivation (`vidyut-prakriya`). `kmadathil/sanskrit_parser` performs
dynamic-programming sandhi-split search over real text, producing a DAG of
valid segmentations that is then constrained into a projective dependency
graph of kāraka relations — the closest existing system to "parse real
Sanskrit text into kāraka frames," and explicit that both over- and
under-generation remain open issues. A separate effort ("Implementing
Pāṇini's Grammar," Language Log, 2023) implements roughly half of the
Aṣṭādhyāyī's ~4,000 rules for word generation, and is explicit that
automatic resolution of rule-application order was not solved — rules were
manually ordered to produce valid output. We treat this as the current
honest state of the art on that specific sub-problem and do not claim to
improve on it (§6).

**Programming languages.** Keyword arguments (Python, Common Lisp) and
named-field structs (Rust) are the closest mainstream analogues to
role-based binding, but each function or struct declares its own local
keyword vocabulary — `host=`, `timeout=`, `retries=` — rather than drawing
from a small, fixed, predicate-independent set. That local-vocabulary
property is exactly what §3.1 argues is the substantive difference from
kāraka roles, not merely a stylistic one. Prolog predicates remain purely
positional, which is the specific gap this paper targets.

To our knowledge, no existing system uses kāraka roles as a general
calling convention for a programming or logic language; the contribution
here is narrow but, as far as we can determine, unoccupied.

## 3. Design: the Kāraka Calling Convention

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
`MERGE` statements against a property graph (e.g. FalkorDB). Both codegen
paths recurse through nested frames, emitting a fresh sub-event identifier
and linking it from the parent by the role name — a Skolemization step, in
the standard logic-programming sense: an existentially-quantified sub-event
("there exists some flooding event that is the instrument here") is
witnessed by a fresh constant rather than left as a bound variable, which
is exactly what turns a nested, tree-shaped `Frame` into flat, indexable
relational tuples without losing the parent-child relationship.

### 3.1 Why this is not just keyword arguments with extra steps

A fair question — raised independently by more than one reader of an
earlier draft — is what a fixed six-role vocabulary buys over ordinary
keyword arguments (`f(agent=x, instrument=y)`), which already give
argument-order independence and human-readable call sites. The answer is
not about readability at the call site, where the two are comparable. It
is about whether the role vocabulary is **shared across predicates** or
**local to each one**.

Python keyword arguments, Rust named fields, and — concretely, since it is
the largest existing system built on argument-role labeling — AMR's
PropBank-derived `:ARG0`–`:ARG5` roles are all *predicate-relative*: each
function, struct, or verb-sense frameset declares its own local mapping
from name to meaning. PropBank makes this explicit in its frameset tables:
`:ARG0` is glossed as "wanter" under the frameset `want-01`, "sleeper"
under `sleep-01`, and "creator" under `develop-02` — three different
meanings for the same label, resolved only by first looking up which
frameset is in play. A kāraka role carries no such indirection: *karta*
denotes "agent" for every predicate, by construction, because the role set
is fixed by the grammar rather than declared per-predicate.

That difference is not aesthetic. It is what makes the rewrite rules in
§4 possible in the general form they take: a rule can be written once
against "any frame with a *karana*" and apply uniformly across every verb
that happens to have an instrument, without first consulting a per-verb
table to find out what that predicate calls its third argument. The same
rule written against keyword arguments or ARG-numbered roles would need
either a separate clause per function/frameset, or a manually maintained
mapping from each local vocabulary back to a shared one — which is,
notably, exactly the kind of mapping kāraka roles are already providing.
The contribution, stated precisely: **a role vocabulary that is fixed and
predicate-independent enables predicate-agnostic rewrite rules**; kāraka
theory is the source of that particular fixed vocabulary and of the
utsarga/apavada discipline for resolving rules once they're written this
way, not the reason the underlying mechanism works.

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
B on any conflicting output. Subset inclusion over these requirement sets
gives a partial order (a poset), not a lattice — we do not define or need
a meet/join over rule requirement sets, only the ability to compare any
two applicable rules, so we do not claim more algebraic structure than is
actually used. If two applicable rules' requirement sets are
incomparable under this order — neither a subset of the other — the engine
raises a structural `AmbiguityError` rather than guessing, mirroring the
way Pāṇinian commentators required an explicit tie-breaking rule when a
conflict didn't resolve by the grammar's own ordering principles. This
closes the composability gap the reviewers identified, though it is worth
noting plainly that the "requirements" a rule declares are still
author-written, not automatically extracted from the `condition` predicate
itself — full automatic subsumption analysis over arbitrary Python
predicates is not attempted, and would be a substantially larger undertaking.

## 5. Implementation and evaluation

The reference implementation (`karaka_lang`, Python) consists of a
tokenizer/role-resolver, the `Frame` AST, two rewrite engines (§4), and
codegen to Prolog and Cypher. A 14-test suite covers: order invariance
across three permutations of a two-role statement; duplicate-role and
missing-verb error handling; a five-role statement (agent, recipient,
instrument, source) modeled on a Rylands v. Fletcher-shaped tort relation;
utsarga/apavada override behavior under both the manual-priority and
subsumption-derived engines, with and without a matching exception
condition; correct rejection of genuinely incomparable rules via
`AmbiguityError`; nested-`Frame` arity extension beyond the six classical
roles; and correctness of both codegen targets under recursion into nested
frames. All 14 tests currently pass. This remains a proof-of-concept
evaluation, not a benchmark — no comparison against Prolog predicate
readability or programmer performance has been conducted (§6).

## 6. Limitations

We list these explicitly rather than in passing, since they bound the
paper's actual claim:

- **Toy morphology.** The reference implementation uses a fixed suffix
  table (a-stem masculine only) rather than real Pāṇinian declension, which
  is stem-class- and gender-dependent. Binding to `vidyut-prakriya` is
  necessary before any claim about real Sanskrit text-processing. This
  remains fully open.
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
  function actually checks. Automatically deriving `requires` from
  arbitrary Python predicates is out of scope; more precisely, it is
  undecidable in general by Rice's theorem (any nontrivial semantic
  property of an arbitrary program is undecidable, and "what frame
  conditions does this predicate check" is such a property) — a
  constrained rule-condition DSL, rather than arbitrary code, would make it
  tractable, at the cost of expressiveness.
- **No human-subject or performance evaluation.** All claims about
  readability improvements over positional Prolog predicates are argued,
  not measured.
- **No claim of general-purpose applicability.** Kāraka roles say nothing
  about control flow, mutation, or concurrency; this is a
  declarative/relational calling convention, not a general-purpose language
  design.

## 7. Future work

Priority order, roughly by architectural payoff, updated after addressing
two of the original four items: (1) replace toy morphology with
`vidyut-prakriya` bindings; (2) replace whitespace tokenization with real
sandhi-aware segmentation; (3) extend the subsumption engine's fact
extraction to recurse into nested sub-frames, so rules can condition on
sub-event properties, not just top-level ones; (4) commit to a single
execution semantics (most plausibly property-graph query/traversal, given
§3) rather than illustrating two codegen targets; (5) a small
human-evaluation study comparing KCC-style relational fact readability
against positional Prolog predicates at matched arity, to move the central
readability claim from argued to measured. (Items 3 and 4 in the original
version of this list — nested-frame arity and subsumption-derived rule
ordering — are now implemented; see §3, §4, §6.)

## 8. Conclusion

The contribution here is intentionally narrow: kāraka roles, evaluated
purely as an argument-binding convention for relational/logic programming,
independent of any claim about Sanskrit as a general-purpose programming
substrate. The proof-of-concept demonstrates the core property (order
invariance) holds by construction and that the resulting representation
compiles naturally to both logic-programming and graph-database targets.
Whether this constitutes a meaningful readability or maintainability
improvement over existing keyword-argument or named-struct conventions in
mainstream languages remains an open, measurable question rather than a
settled one.

## References

- Briggs, R. (1985). Knowledge Representation in Sanskrit and Artificial
  Intelligence. *AI Magazine*, 6(1), 32–39.
- Fillmore, C. J. (1968). The Case for Case. In *Universals in Linguistic
  Theory*, Holt, Rinehart and Winston.
- Fillmore, C. J. (1976). Frame Semantics and the Nature of Language.
  *Annals of the New York Academy of Sciences*, 280(1), 20–32.
- Minsky, M. (1974). A Framework for Representing Knowledge. MIT-AI
  Laboratory Memo 306.
- Banarescu, L. et al. (2013). Abstract Meaning Representation for
  Sembanking. *Proceedings of the 7th Linguistic Annotation Workshop and
  Interoperability with Discourse*.
- Kingsbury, P. & Palmer, M. (2002). From Treebank to PropBank.
  *Proceedings of LREC*.
- Huet, G. Sanskrit Heritage Engine.
- Ambuda Project. `vidyut`: segmentation, sandhi, and Ashtadhyayi-based
  word derivation. https://github.com/ambuda-org/vidyut
- Madathil, K. et al. `sanskrit_parser`.
  https://github.com/kmadathil/sanskrit_parser
- "Implementing Pāṇini's Grammar." Language Log, 2023.
  https://languagelog.ldc.upenn.edu/nll/?p=61507
