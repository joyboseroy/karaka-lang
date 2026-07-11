# Why Prolog Predicates Fall Apart — and What a 2,500-Year-Old Grammar Has to Say About It

If you've ever debugged a Prolog predicate with six arguments, you know the
specific kind of pain this article is about. `causes_harm(X, Y, Z, W, V, U)`
compiles fine. Reading it back a week later, you have no idea which
variable was the person responsible, which was the thing that got damaged,
and which was the tool that did the damage. The arity grew, and the meaning
of each slot became something you had to remember rather than something you
could read.

This isn't a Prolog-specific failure. It's what happens to *any* language
where an argument's meaning comes from its position in a list. Python and
Rust patched around this with keyword arguments and named structs. Prolog,
for the most part, didn't.

There's a 2,500-year-old fix for this problem, and it wasn't designed for
computers.

## Pāṇini's other invention

Sometime around the 4th century BCE, the grammarian Pāṇini wrote a
description of Sanskrit — the *Aṣṭādhyāyī* — that's still cited in
linguistics and, increasingly, in computer science, because it's built like
a formal system: around 4,000 compact rules, applied in a defined order,
generating every valid word form in the language. People have called it one
of the first generative grammars, full stop, not just "generative grammar
for a natural language."

One piece of that system is what's called *kāraka* theory: six semantic
roles — agent, object, instrument, recipient, source, and location — that
get attached to nouns through case endings. Say a sentence like "a leaf
falls from a tree to the ground because of the wind," and Pāṇinian grammar
doesn't care what order you say it in. "Wind," marked with the instrumental
case ending, is unambiguously the *instrument* no matter where it sits in
the sentence. "Tree," marked ablative, is unambiguously the *source*. Word
order in Sanskrit carries almost no grammatical weight, because the case
endings already did the job that word order does in English.

In 1985, a NASA researcher named Rick Briggs published a paper in *AI
Magazine* pointing out that this is, structurally, a semantic net — the
exact kind of knowledge representation AI researchers were hand-building at
the time. It's a genuinely interesting paper. It's also been dragged into a
much sillier internet myth over the decades — no, NASA did not declare
Sanskrit "the only unambiguous language for computers," that's a
nationalist embellishment that outran the actual claim. The actual claim is
narrower and more useful: *case-marked roles let you drop word order
without losing meaning.*

## What that buys you as a calling convention

Here's the part that isn't about Sanskrit as a human language at all. If
you take those six roles and use them as an **argument-binding convention**
for a logic language instead of a natural one, you get predicates whose
arguments are self-describing:

```
manah ksetraya jalena jalasayat harati
```

"The man, to-the-field, by-means-of-the-flood, from-the-reservoir, causes
harm." Every argument carries its own role marker. You can shuffle the
words into any order and it parses to the *same* structure — I checked this
with an assertion in a test suite, not just by eyeballing it:

```
Frame(hara, karta=man, sampradana=field, karana=flood, apadana=reservoir)
```

Compare that to `causes_harm(man, field, flood, reservoir)` and imagine
finding that predicate again in six months.

And there's a second thing this buys you almost for free: that `Frame` —
verb plus role-labeled arguments — is already a small graph. One event
node, labeled edges out to each argument. Which means it compiles cleanly
in two directions at once: to normalized Prolog facts (`karta(e1, man).
karana(e1, flood).`, which stays readable no matter how many roles you add,
unlike a positional term) and to Cypher `MERGE` statements for a graph
database, from the exact same source object. You don't have to choose one
representation over the other — a role-labeled relation is native to both.

## The part I'm not claiming

I want to be upfront about what this is and isn't, because it's easy to
overclaim on a topic like this and there's a long history of people doing
exactly that.

This is not a claim that Sanskrit is a superior programming language in
general. It's not a claim about performance, or safety, or being more
"AI-native" — those words show up a lot in casual discussion of this idea
and mean approximately nothing without a benchmark attached. Kāraka roles
have nothing to say about loops, mutation, or concurrency; this only
addresses argument binding in declarative, relational code, which is a
real but narrow slice of what programming languages need to do.

It's also not a claim to have solved Pāṇinian rule-ordering — the general
problem of automatically deciding which of several matching grammar rules
should win. Even the most complete existing software implementations of the
Aṣṭādhyāyī (a project that's implemented roughly half of its 4,000 rules)
are explicit that they hand-order rules to get correct output rather than
deriving the order automatically. I did the same thing here, with a small
rewrite-rule engine that mirrors Pāṇini's own general-rule-then-exception
principle (*utsarga* and *apavada* — a general "strict liability" rule
fires, then a more specific "instrument-based liability" rule overrides it
if it applies) using an explicit priority number rather than pretending to
have automated it.

What's left is a narrow, testable claim: kāraka roles work as an
order-independent argument-binding convention because the role vocabulary
is fixed and shared across every predicate — unlike keyword arguments, and
unlike PropBank's ARG0–ARG5 roles, which are redefined per verb sense.
That's the one-sentence version of the actual theoretical argument, worked
out in more detail in the position paper. It fixes a specific,
long-standing readability problem in positional logic programming, and it
falls out naturally into graph representations. That's a smaller claim
than "Sanskrit for AI," but it's one I can actually back with a passing
test suite instead of a slogan.

The code, tests, and a longer technical write-up with the full related-work
review are in the repo linked below, if you want to see whether the claim
holds up.
