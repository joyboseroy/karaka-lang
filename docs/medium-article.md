# I Used a 2,500-Year-Old Sanskrit Grammar to Fix a Modern Programming Problem

*Revised and expanded. Since first publishing this, the project gained real Paninian morphology, a query mode, and nine more tests, and readers asked some sharp questions that the original did not answer well. This version answers them.*

Programming languages still argue about arguments. Prolog, Python, Rust, all of them have to answer one basic question: when you call a function with five or six inputs, how does the computer know which input means what?

Most languages answer this with position. The first thing you pass is the first thing. The second thing is the second thing. This works fine until the argument count grows, and then it quietly turns into a memory test for every programmer who reads the code later.

Sanskrit solved a version of this problem a very long time ago. Not for computers, for sentences. And it turns out the solution translates surprisingly well.

This post explains why I went looking at Sanskrit grammar specifically, what earlier attempts at "Sanskrit programming languages" got wrong, and walks through a small working project I built called karaka-lang. Code, tests, and a full position paper are all in the GitHub repo linked at the end, so you can run it yourself.

## Why this problem is real

Here is what a six-argument Prolog predicate looks like:

```prolog
causes_harm(X, Y, Z, W, V, U).
```

If you did not write this line yourself, you have no idea what `X` through `U` mean. Is `X` the person responsible? The thing that got damaged? The date it happened? You have to go find the definition and count positions to find out.

Python and Rust patched around this problem with keyword arguments and named fields. You can write:

```python
connect(host="db.local", port=5432, timeout=30)
```

instead of:

```python
connect("db.local", 5432, 30)
```

and now it reads fine.

But here is the catch: those keyword names are local to that one function. `host=` only means something inside `connect()`. Every function invents its own private vocabulary of argument names. There is no shared, predictable set of roles across your whole codebase. A rule engine or a static analysis tool cannot look at an arbitrary function call and know "this is the recipient" the way it can with, say, a type.

## Why Sanskrit specifically

Around the 4th century BCE, a grammarian named Panini wrote a description of Sanskrit called the Ashtadhyayi. It is roughly 4,000 short rules that generate every valid word form in the language. Linguists and computer scientists both cite it as one of the earliest known examples of a formal, rule-based generative grammar: the same basic idea behind a modern compiler grammar, just built for a human language two and a half thousand years earlier.

One part of that system is called karaka theory. Sanskrit nouns take different endings depending on their grammatical role in a sentence:

- who did the action (agent)
- what it was done to (object)
- what tool was used (instrument)
- who received something (recipient)
- where something came from (source)
- where something happened (location)

These six roles are marked directly on the word itself through its case ending, not through word order.

This has a strange side effect. Because the role is stamped onto each word, word order barely matters. You can say "the man causes harm to the field by means of the flood" in almost any order of those five words and it still parses the same way, because "by means of" is welded onto "flood" no matter where you put it in the sentence.

In 1985, a NASA researcher named Rick Briggs wrote a paper pointing out that this is structurally very close to a semantic network, which is exactly the kind of data structure AI researchers were hand-building at the time to represent facts and relationships. That paper is genuinely interesting and worth reading. It is also the source of an exaggerated internet myth that NASA declared Sanskrit "the only unambiguous language for computers." That never happened. The real paper makes a much narrower and more useful point: case-marked roles let you drop word order without losing meaning. That is the part worth taking seriously, and the part I focused on.

## What previous attempts got wrong

Search "Sanskrit programming language" and you will find a handful of small projects on GitHub. Almost all of them make the same mistake: they take an existing language like Python or a C-style language, and translate the keywords into transliterated Sanskrit words. `if` becomes `yadi`. `function` becomes `karya`. The actual syntax underneath, the part that decides how arguments are passed and how the parser reads the code, stays exactly the same as before.

This misses the entire point. Swapping `if` for `yadi` does not use anything structural about Sanskrit grammar. It is a find-and-replace on keywords, not a new design.

On the other side, there is real, serious computational Sanskrit work that has nothing to do with programming languages at all. A few worth knowing about:

- Gerard Huet's Sanskrit Heritage Engine, one of the original computational models of Panini's grammar, built for parsing and generating real Sanskrit text.
- vidyut, an actively maintained project by the Ambuda group, which handles word segmentation, sandhi (the sound changes that happen when words merge together), and is in the process of implementing the Ashtadhyayi's actual word-formation rules.
- sanskrit_parser by Karthik Madathil, which searches through all the ways a merged Sanskrit sentence could be split back into words, then builds a dependency graph of the karaka relationships between them.
- A project documented on the blog Language Log that implemented roughly half of the Ashtadhyayi's 4,000 rules in Rust, for generating Sanskrit word forms. The author is honest that the hardest part, deciding which rule to apply when several could apply, was not solved automatically. Rules were manually ordered by hand to get correct output.

None of these projects are trying to build a general-purpose programming language. And none of the cosmetic keyword-translation projects use the real linguistic ideas these serious projects are built on. There is a real gap between the two, and that gap is what I wanted to build something in.

One honest update since first publishing: a prior-art search later found I was not alone in that gap. A Devanagari-first language called Karaka, by Sunil Prakash, appeared on the Rust package registry within weeks of this work, using the same six roles as call-site labels in an imperative language. I verified this from its published source code, and the formal paper in the repo now contains a precise comparison. Two independent implementations in the same season is evidence the idea is in the air, and what follows is what this version does that his does not: morphological role marking, compilation to logic facts and graph databases, a rule engine, and a query mode.

## What I actually built

The idea: what if the six karaka roles became a calling convention for a logic programming language, completely separate from any claim about Sanskrit being a good general-purpose language for humans to write?

A statement in this toy language looks like this:

```
manah ksetraya jalena jalasayat harati
```

Word for word: man (agent marker), field (recipient marker), flood (instrument marker), reservoir (source marker), causes-harm.

This parses into what I call a Frame:

```
Frame(hara, karta=man, sampradana=field, karana=flood, apadana=reservoir)
```

`karta` is the agent role, `sampradana` is the recipient, `karana` is the instrument, `apadana` is the source. Every argument carries its own role tag, so you can put the words in any order and get the exact same Frame back. I tested this directly: three different word orders of the same sentence produce an identical parsed result.

## Why this is different from just using keyword arguments

This is the question I got asked the most while working on this, so it deserves a direct answer.

The difference is not about readability at the call site. `foo(agent=x, instrument=y)` is already readable. The difference is whether the role names are shared across every function in your program, or invented separately by each one.

Python's keyword names, Rust's named fields, and even PropBank's numbered argument roles (used heavily in modern NLP, in a system called Abstract Meaning Representation) are all local to whatever function or verb sense you are looking at. PropBank actually makes this explicit: their `:ARG0` role means "the wanter" for the verb sense `want-01`, "the sleeper" for `sleep-01`, and "the creator" for `develop-02`. Same label, three different meanings, and you have to go look up the specific verb sense to know which one applies.

A karaka role does not have this problem. `karta` means "the agent" for every predicate in the language, by construction. Because the vocabulary is fixed and shared, you can write a rule like "for any event that has a `karana`, do X" and it applies uniformly across your whole program, without needing a lookup table to translate each function's private argument names back to a common vocabulary first.

Since first publishing, that claim now has a working demonstration in the test suite instead of just an argument. One rule, mentioning no verb at all, requiring only that an instrument and a recipient are present, applied to two frames under completely different verbs, causing-harm and giving:

```
Frame(hara, class=mediated-transfer, karana=jal, karta=man, sampradana=ksetr)
Frame(dada, class=mediated-transfer, karana=dhan, karta=nar, sampradana=putr)
```

Both classified by one rule that knows nothing about either verb. Written against keyword arguments, this needs a separate clause per function, or a maintained mapping from every function's private names back to shared ones. And a mapping from private names to shared roles is a karaka layer, reinvented.

## When this is not worth using

Readers pushed back with three questions sharp enough that they mark the real boundary of this idea, so they deserve their own section.

**"Why should all functions have the same parameters?"** They should not, and nothing here requires it. A motion event binds two roles. The tort example above binds four. Predicates take however many roles they genuinely have. The claim is only that when a predicate has an agent, it calls that argument `karta` instead of inventing a private name for it. Shared vocabulary, not shared arity.

**"Can all functions be reduced to karakas?"** No. Karakas are participant roles in events: who acted, on what, with what, from where. `connect(host, port, timeout)` has no agent and no instrument in any honest sense; a timeout is not a participant in anything. Forcing it into a karaka would repeat the keyword-translation mistake one level deeper. This is exactly why the project restricts itself to relational and logic programming: legal facts, provenance records, knowledge graphs, who-did-what-to-whom data. For configuration-style parameters, ordinary keyword arguments are simply better, and I will not pretend otherwise.

**"Doesn't a programmer have to learn Sanskrit grammar? And your `Frame(hara, karta=man, ...)` looks exactly like keyword arguments anyway."** Both fair. Nobody needs to learn declension or sandhi to use this: the roles in code are seven ASCII words, and the Sanskrit morphology layer is optional. And yes, the Frame syntax is indistinguishable from keyword arguments. The entire difference is the one property demonstrated above: the names are a closed set with fixed meanings across every predicate, so cross-predicate rules and queries become writable.

So the honest framing is not "karaka beats flexible parameters." It is a trade: you give up naming freedom and get cross-predicate operability. The restriction is the feature, the same way a database schema or a standard vocabulary like schema.org is a feature. Single-author code with no rule layer and no graph gains nothing from the trade, and there the flexibility of current languages wins. Anything where independent predicates must interoperate is where it starts paying.

## The arity problem, and how I solved it

Six roles is not enough for real software. A database connection function alone might need a host, port, timeout, retry count, and more.

The fix: a role does not have to point to a plain value. It can point to an entire nested Frame instead. So "instrument" does not have to be a simple word like "flood." It can be its own sub-event, like "a flood caused by heavy rainfall," which is itself a Frame with its own agent and roles. This removes the fixed six-role ceiling without inventing more roles. It is the same idea Sanskrit grammar uses for compound expressions, just applied recursively.

## Rule conflicts, the Sanskrit way

Panini's grammar has a built-in way of resolving conflicts: a general rule applies by default, and a more specific exception rule overrides it when it also applies. This is called utsarga (general rule) and apavada (exception), and it is the same basic idea as CSS specificity, where a more specific selector wins.

My first version of this used a plain priority number that you set by hand on each rule, which works but does not scale. If two people independently write rules and both pick `priority=5`, combining their rule sets gives you an arbitrary, meaningless order.

The current version fixes this. Each rule declares which conditions it needs to match (for example, "the verb is `hara` and there is a `karana` role present"). A rule is automatically considered more specific if its conditions are a strict superset of another matching rule's conditions, and the more specific one wins. If two rules match the same input and neither one's conditions are a superset of the other's, the system does not guess. It raises an error and tells you to write a rule that resolves the conflict explicitly. This mirrors how Sanskrit grammar commentators historically handled genuinely ambiguous rule conflicts: not by picking arbitrarily, but by requiring an explicit tie-breaking rule.

## Running it yourself

Everything below is copy-pasteable and I ran it myself before writing this post.

Clone the repo and install it:

```bash
git clone https://github.com/joyboseroy/karaka-lang.git
cd karaka-lang
pip install -e ".[dev]"
pip install vidyut   # optional: real Ashtadhyayi morphology
```

Run the test suite (23 tests; 3 skip cleanly if the optional vidyut package is not installed):

```bash
pytest
```

Try the order-invariance demo:

```bash
python3 examples/robot_kitchen.py
```

Output:

```text
'robotah pakasthanam gacchati'           -> Frame(gaccha, karma=pakasthan, karta=robot)
'gacchati robotah pakasthanam'           -> Frame(gaccha, karma=pakasthan, karta=robot)
'pakasthanam robotah gacchati'           -> Frame(gaccha, karma=pakasthan, karta=robot)

All three orders parsed to an identical Frame.
```

Try the legal-relation example, which shows multi-role parsing, rule resolution, and code generation to both Prolog and Cypher (the query language for graph databases like FalkorDB) from the same parsed object:

```bash
python3 examples/rylands_fletcher.py
```

Output:

```text
Parsed frame: Frame(hara, apadana=jalasay, karana=jal, karta=man, sampradana=ksetr)
Resolved frame: Frame(hara, apadana=jalasay, karana=jal, karta=man, liability=instrument-based, sampradana=ksetr)

-- Prolog --
event(e1, hara).
apadana(e1, jalasay).
karana(e1, jal).
karta(e1, man).
liability(e1, instrument-based).
sampradana(e1, ksetr).

-- Cypher (FalkorDB) --
MERGE (e:Event {verb: "hara"})
MERGE (n_jalasay:Entity {name: "jalasay"}) MERGE (e)-[:APADANA]->(n_jalasay)
MERGE (n_jal:Entity {name: "jal"}) MERGE (e)-[:KARANA]->(n_jal)
MERGE (n_man:Entity {name: "man"}) MERGE (e)-[:KARTA]->(n_man)
MERGE (n_instrument-based:Entity {name: "instrument-based"}) MERGE (e)-[:LIABILITY]->(n_instrument-based)
MERGE (n_ksetr:Entity {name: "ksetr"}) MERGE (e)-[:SAMPRADANA]->(n_ksetr)
```

There are two more examples: `examples/arity_and_ordering_fixes.py`, which shows the nested-frame arity fix and the rule engine correctly refusing to guess on a genuinely ambiguous rule conflict, and `examples/real_morphology_and_queries.py`, which shows the real morphology and query mode described below.

## Why the Frame compiles to both Prolog and a graph database

This part is not a coincidence. A Frame is a verb plus a set of role-labeled arguments. That is already the shape of a small graph: one event node, with labeled edges going out to each argument. So it compiles cleanly to normalized Prolog facts (one line per role, which stays readable no matter how many roles you add, unlike a positional term) and just as cleanly to a graph database write, from the exact same object. You are not translating between two different representations. Both outputs are just different projections of the same underlying shape.

## What this is not

I want to be direct about the limits, because it is easy to overclaim on a topic like this and there is a long history of people doing exactly that.

This is not a claim that Sanskrit is a better general-purpose programming language. It says nothing about loops, mutation, or concurrency. It only addresses how arguments get bound to a relation, which is a real but narrow slice of what a language needs to do.

The graph output is faithful on the way in, but not guarded on the way out. The parser enforces one agent per event and a closed role set, and the compiled writes respect that. But a graph database will not stop a later writer from attaching two agents to the same event, so the schema honesty lives in the compiler, not the store. If relationship-type integrity matters in your graph, that enforcement is still your job downstream.

The tokenizer here splits on whitespace. Real Sanskrit text merges word boundaries together through sandhi, which is a genuine search problem, not something you get for free. Projects like vidyut and sanskrit_parser handle this properly, and a real version of this project should use one of them.

There is no user study yet showing this is actually easier to read than positional Prolog. That claim is argued in the paper, not measured. It is the single biggest piece of evidence still missing.

## Update: the morphology became real

The first version of this article admitted the morphology was a toy suffix table and said a real implementation would connect to vidyut-prakriya instead of reinventing it. That has now happened. With `pip install vidyut`, declined forms are generated through the real Ashtadhyayi rule engine, and every analyzed word carries the exact sutra numbers that derived it:

```text
aSvena = aSva + Trtiya (karana), derived by sutras:
  1.2.45 -> 4.1.2 -> 1.3.7 -> 1.3.9 -> 1.4.13
  -> 7.1.12 -> 1.4.18 -> 1.4.14 -> 6.1.87 -> 8.4.68
```

That is "by horse," resolved to the instrument role through ten traced steps of Panini's actual grammar. A detail I enjoyed: while testing, I misspelled "horse" with the wrong sibilant, and the rule engine correctly produced a different word form through a real retroflexion rule. The 2,500-year-old grammar caught my typo.

It works over a registered lexicon (a symbol table, which is normal for a programming language), singular forms, and the default case-to-role mapping. The toy parser remains the zero-dependency fallback. There is also the query mode mentioned above: leave a role open with a variable like `?kah` (who?) and the same Frame compiles to a database query instead of a write. See `examples/real_morphology_and_queries.py` and `docs/ROADMAP.md` in the repo.

## Where to go from here

The full code, all 23 tests, four runnable examples, an in-depth design document, and a formal paper with a full literature review, including the precise comparison with Prakash's Karaka, are all in the repository:

**[github.com/joyboseroy/karaka-lang](https://github.com/joyboseroy/karaka-lang)**

If you build on this, or find a hole in the reasoning, I would genuinely like to hear about it. The best parts of this revision came from exactly that.
