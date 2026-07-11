"""
parser.py -- tokenizer and kāraka resolver.

This uses a small, fixed, ASCII-transliterated suffix set inspired by the
six kāraka case endings. It is deliberately NOT a full Sanskrit
morphological engine -- that problem is already being solved properly by
vidyut-prakriya (github.com/ambuda-org/vidyut), which implements the
Ashtadhyayi's actual declension rules (stem-class and gender dependent).
Reimplementing that here would be both worse and pointless; see
docs/DESIGN.md section 6 for how to swap this module for real morphology.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

# Toy karaka suffix table -- every stem is treated as an a-stem masculine,
# which is enough to demonstrate the calling convention itself.
KARAKA_SUFFIXES = {
    "ah":  "karta",       # agent      (nominative,  robotah  "the robot")
    "am":  "karma",       # object     (accusative,  sthanam  "the place")
    "ena": "karana",      # instrument (instrumental, dandena "by the stick")
    "aya": "sampradana",  # recipient  (dative,       narAya   "to the person")
    "at":  "apadana",     # source     (ablative,     grAmAt   "from the village")
    "e":   "adhikarana",  # locus      (locative,     grhe     "in the house")
    "sya": "sambandha",   # possessor  (genitive,     rAjasya  "of the king")
}

_SUFFIXES_BY_LENGTH = sorted(KARAKA_SUFFIXES, key=len, reverse=True)
VERB_MARKER = "ti"  # toy 3rd-person-singular-present marker, e.g. gacchati


@dataclass
class Token:
    surface: str
    stem: str
    role: Optional[str]
    is_verb: bool = False


def tokenize(sentence: str) -> list[Token]:
    """Split whitespace-separated words and resolve each to a kāraka role
    by matching its suffix. A real implementation replaces this with
    vidyut-cheda-style sandhi segmentation + morphological tagging --
    word boundaries in real text aren't whitespace-delimited."""
    tokens = []
    for word in sentence.strip().split():
        word_clean = word.strip(",.")
        if word_clean.endswith(VERB_MARKER):
            tokens.append(Token(surface=word_clean, stem=word_clean[:-len(VERB_MARKER)],
                                 role=None, is_verb=True))
            continue
        matched = False
        for suf in _SUFFIXES_BY_LENGTH:
            if word_clean.endswith(suf) and len(word_clean) > len(suf):
                stem = word_clean[: -len(suf)]
                tokens.append(Token(surface=word_clean, stem=stem,
                                     role=KARAKA_SUFFIXES[suf]))
                matched = True
                break
        if not matched:
            raise ValueError(f"Cannot resolve karaka role for word: {word_clean!r}")
    return tokens


@dataclass
class Frame:
    """A single relation: a verb plus its role-bound arguments. This *is*
    the AST node, and it is also, not coincidentally, a labeled-edge graph
    fragment: (verb) --role--> (argument). See docs/DESIGN.md section 3 on
    why this compiles naturally to both Prolog and property-graph writes.

    A role's value is normally a leaf string (an entity name), but it can
    also be another Frame -- a sub-event nested under a role, most
    naturally under `sambandha` (genitive/possessive), the traditional
    Paninian overflow role. This is how arity beyond the six classical
    kārakas is handled: not by adding more roles, but by letting any role
    point to an entire sub-relation instead of a leaf. `parse()` only ever
    produces leaf-valued frames from flat surface text (the toy tokenizer
    has no surface syntax for nesting); nested frames are built
    programmatically, the same way a real system would build them by
    resolving a `sambandha`-marked argument's own predicate structure."""
    verb: str
    roles: dict[str, "str | Frame"] = field(default_factory=dict)

    def __repr__(self):
        def fmt(v):
            return repr(v) if isinstance(v, Frame) else str(v)
        args = ", ".join(f"{r}={fmt(v)}" for r, v in sorted(self.roles.items(), key=lambda kv: kv[0]))
        return f"Frame({self.verb}, {args})"

    def is_leaf(self, role: str) -> bool:
        return not isinstance(self.roles.get(role), Frame)


def parse(sentence: str) -> Frame:
    """Parse a surface sentence into a Frame. Word order does not affect
    the result -- every argument carries its own role marker."""
    tokens = tokenize(sentence)
    verbs = [t for t in tokens if t.is_verb]
    if len(verbs) != 1:
        raise ValueError(f"Expected exactly one verb, found {len(verbs)}")
    verb = verbs[0].stem
    roles: dict[str, str] = {}
    for t in tokens:
        if t.is_verb:
            continue
        if t.role in roles:
            raise ValueError(f"Duplicate karaka role '{t.role}' in frame")
        roles[t.role] = t.stem
    return Frame(verb=verb, roles=roles)
