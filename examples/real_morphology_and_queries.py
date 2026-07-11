"""
Real Paninian morphology (via vidyut-prakriya) + query mode.

Requires: pip install vidyut

Every declined form here is generated through the actual Ashtadhyayi rule
engine, not the toy suffix table, and every analysis can print the exact
sutra numbers that derived it.
"""
from karaka_lang import HAS_VIDYUT, parse, compile_frame

if not HAS_VIDYUT:
    raise SystemExit("This example needs vidyut: pip install vidyut")

from karaka_lang import VidyutResolver

# --- 1. Build a lexicon; vidyut derives every declined form ---------------

r = VidyutResolver()
r.add_stems({"nara": "Pum", "grAma": "Pum", "aSva": "Pum"})

print("=== Real Ashtadhyayi derivation, with sutra trace ===")
print(r.explain("aSvena"))
print()

# --- 2. Parse a real declined sentence into a Frame -----------------------

# naraH grAmam aSvena gacCati : "the man goes to the village by horse"
frame = r.parse("naraH grAmam aSvena gacCati", verb_forms={"gacCati": "gam"})
print("=== Parsed frame (real morphology) ===")
print(frame)
print()

# --- 3. Query mode: leave a role open, get a query instead of a write -----

print("=== Assertion vs. query from the same Frame type ===")
assertion = parse("robotah pakasthanam gacchati")
question = parse("?kah pakasthanam gacchati")   # WHO goes to the kitchen?

print("Assertion compiles to a write:")
print(compile_frame(assertion, target="cypher"))
print()
print("Question compiles to a query:")
print(compile_frame(question, target="cypher"))
print()
print("Same question as a Prolog goal:")
print(compile_frame(question, target="prolog"))
