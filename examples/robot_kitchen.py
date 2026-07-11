"""Order invariance: three word orders, one Frame."""
from karaka_lang import parse

variants = [
    "robotah pakasthanam gacchati",   # robot-NOM kitchen-ACC go
    "gacchati robotah pakasthanam",   # go robot-NOM kitchen-ACC
    "pakasthanam robotah gacchati",   # kitchen-ACC robot-NOM go
]

for v in variants:
    print(f"{v!r:40} -> {parse(v)}")

assert len({repr(parse(v)) for v in variants}) == 1
print("\nAll three orders parsed to an identical Frame.")
