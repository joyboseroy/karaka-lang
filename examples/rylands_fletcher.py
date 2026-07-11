"""
A Rylands v. Fletcher-shaped statement: an agent causes harm to a recipient
by means of an instrument, from a source. Demonstrates multi-role binding,
utsarga/apavada rule resolution, and dual codegen (Prolog + Cypher) from the
same Frame -- relevant to a case-graph legal-AI pipeline where the same
underlying relation needs both queryable facts and a graph representation.
"""
from karaka_lang import parse, Sutra, SutraEngine, to_prolog, to_cypher, Frame

frame = parse("manah ksetraya jalena jalasayat harati")
print("Parsed frame:", frame)

engine = SutraEngine()
engine.add(Sutra(
    name="default-liability",              # utsarga: general rule
    condition=lambda f: f.verb == "hara",
    transform=lambda f: Frame(f.verb, {**f.roles, "liability": "strict"}),
    specificity=0,
))
engine.add(Sutra(
    name="instrument-liability-exception",  # apavada: exception, overrides
    condition=lambda f: f.verb == "hara" and "karana" in f.roles,
    transform=lambda f: Frame(f.verb, {**f.roles, "liability": "instrument-based"}),
    specificity=1,
))

resolved = engine.apply(frame)
print("Resolved frame:", resolved)

print("\n-- Prolog --")
print(to_prolog(resolved, event_id="e1"))

print("\n-- Cypher (FalkorDB) --")
print(to_cypher(resolved))
