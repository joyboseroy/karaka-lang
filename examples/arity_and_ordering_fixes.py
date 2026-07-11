"""
Demonstrates the two fixes added in response to reviewer feedback on the
position paper:

1. Arity beyond six roles, via a nested Frame under a role instead of a
   flat leaf string.
2. Rule-conflict resolution derived from condition subsumption instead of
   an author-assigned integer, including a case where the engine correctly
   refuses to guess.
"""
from karaka_lang import (
    Frame, to_prolog, to_cypher,
    SubsumptionSutra, SubsumptionEngine, AmbiguityError,
)

# --- 1. Arity fix: instrument is itself an event, not a leaf -----------

rainfall = Frame("varsa", {"karta": "megh"})          # "the cloud rains"
flood = Frame("hara", {                                 # "causes harm"
    "karta": "man",
    "sampradana": "field",
    "karana": rainfall,      # nested Frame, not a string -- extends arity
    "apadana": "reservoir",
})

print("Nested frame:", flood)
print("\nProlog (recurses into the sub-event):")
print(to_prolog(flood, event_id="e1"))
print("\nCypher (sub-event becomes its own :Event node):")
print(to_cypher(flood))

# --- 2. Ordering fix: subsumption-derived specificity -------------------

print("\n--- Subsumption engine ---")
engine = SubsumptionEngine()
engine.add(SubsumptionSutra(
    name="default-liability",
    requires=frozenset({"verb=hara"}),
    transform=lambda f: Frame(f.verb, {**f.roles, "liability": "strict"}),
))
engine.add(SubsumptionSutra(
    name="instrument-liability-exception",
    requires=frozenset({"verb=hara", "has:karana"}),  # strict superset -> apavada
    transform=lambda f: Frame(f.verb, {**f.roles, "liability": "instrument-based"}),
))
resolved = engine.apply(flood)
print("Resolved liability:", resolved.roles["liability"])

# Two incomparable rules matching the same frame -- the engine refuses to
# silently pick a winner, instead of a manual-priority engine which would.
print("\n--- Genuine ambiguity: engine refuses to guess ---")
ambiguous_engine = SubsumptionEngine()
ambiguous_engine.add(SubsumptionSutra(
    name="rule-a", requires=frozenset({"verb=hara", "has:karana"}),
    transform=lambda f: Frame(f.verb, {**f.roles, "tag": "a"}),
))
ambiguous_engine.add(SubsumptionSutra(
    name="rule-b", requires=frozenset({"verb=hara", "has:sampradana"}),
    transform=lambda f: Frame(f.verb, {**f.roles, "tag": "b"}),
))
try:
    ambiguous_engine.apply(flood)
except AmbiguityError as e:
    print(f"AmbiguityError (correctly raised): {e}")
