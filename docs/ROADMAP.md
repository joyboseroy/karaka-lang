# Roadmap: from toy to tool

Status of each item from the position paper's roadmap (§7), plus what
comes after. Updated as of v0.3.0.

## Done

**Real Paninian morphology (was: roadmap item 1).**
`karaka_lang/morphology.py` binds to `vidyut-prakriya`. Declined forms are
generated through the actual Ashtadhyayi rule engine (analysis-by-generation
over a registered lexicon), and every analysis carries its full sutra
derivation trace. `aSvena` resolves to `aSva + Trtiya -> karana` with the
rule chain `1.2.45 -> 4.1.2 -> ... -> 8.4.68` attached. The toy suffix
table remains the zero-dependency fallback. Honest scope: closed lexicon
(a symbol table, which is normal for a programming language), singular
forms, and a default vibhakti-to-karaka mapping that a production system
would condition on the verb (passives and verbs governing unusual cases
break the neat one-to-one mapping).

**Rules over nested sub-events (was: roadmap item 3).**
`SubsumptionEngine` fact extraction now recurses into nested frames with
path-prefixed facts (`karana.verb=varsa`), so a rule can require "the
instrument is itself a rainfall event." Tested.

**Query mode (new, beyond the original roadmap).**
A role can be a variable (`?kah` = who?). A frame with any variable
compiles to a Cypher `MATCH ... RETURN` or a Prolog goal instead of a
write; `compile_frame()` dispatches automatically. This is the step that
makes the Frame a program element rather than a serialization format: the
same structure expresses assertion and question, the way Prolog facts and
goals do, but role-labeled.

## Next, in rough order of payoff per effort

**1. Execute queries against a real FalkorDB instance.** The Cypher
output is currently text. Wire `compile_frame` output to the `falkordb`
Python client, assert a small fact base, run the generated `MATCH`
queries, return bindings. A weekend of work; turns "compiles to Cypher"
into "runs."

**2. Sandhi-aware input via vidyut-cheda.** Accept real merged Sanskrit
text instead of whitespace-separated words. `vidyut.cheda` provides the
segmenter; it needs vidyut's downloadable linguistic data
(`vidyut.download_data`). The integration is straightforward; the honest
complication is that segmentation is ambiguous and the parser will need
to surface multiple candidate segmentations rather than one answer.

**3. Verb-conditioned role mapping.** The current vibhakti-to-karaka map
is the default correspondence. Real Sanskrit verbs govern cases
idiosyncratically, and passives invert the mapping. A per-verb table
(the same shape as PropBank framesets, ironically) fixes this, and
vidyut's dhatupatha data can seed it.

**4. Plural and dual.** `VidyutResolver` currently generates singular
only. Adding `Vacana.Dvi` and `Vacana.Bahu` is mechanical; deciding what
plurality means for the calling convention (a role bound to a set?) is a
small design question worth thinking through first.

**5. The readability study.** Still the biggest missing piece of
evidence, per the position paper's own §6: N participants, matched-arity
positional Prolog vs KCC facts, measure comprehension time and error
rate. Cannot be done by writing more code; needs people. The materials
(paired predicate sets) can be prepared in the repo ahead of time.

**6. arXiv submission.** The position paper is in submittable shape after
the v0.2.0 revisions (related work covers AMR/PropBank, frame semantics,
Datalog/RDF; the keyword-argument objection has a direct answer in §3.1).
Category cs.PL, cross-list cs.CL. The main pre-submission task is
converting to LaTeX and verifying every citation's formatting.

## Explicitly not planned

- General-purpose control flow (loops, mutation). Kāraka roles have
  nothing to say about it, and bolting it on would dilute the one clear
  claim this project has.
- Devanagari surface syntax. Transliteration (SLP1, which vidyut uses
  natively) keeps the toolchain simple; script is presentation, not
  structure.
- Automatic extraction of rule `requires` sets from arbitrary Python
  predicates (undecidable in general; see position paper §6). A
  constrained condition DSL is the tractable version if it's ever needed.
