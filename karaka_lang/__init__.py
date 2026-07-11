"""
karaka_lang -- a Paninian kāraka-based calling convention for logic/relational
programming.

Arguments are bound to a predicate by grammatical role (agent, object,
instrument, recipient, source, locus) instead of by position, which makes
argument order irrelevant to meaning and fixes the arity/mode brittleness of
positional predicates in languages like Prolog.

See docs/DESIGN.md for the architecture and honest scope of what this is
and isn't, and docs/position-paper.md for the research framing.
"""

from .parser import Token, Frame, tokenize, parse, KARAKA_SUFFIXES
from .sutra import Sutra, SutraEngine, SubsumptionSutra, SubsumptionEngine, AmbiguityError
from .codegen import to_prolog, to_cypher

__all__ = [
    "Token", "Frame", "tokenize", "parse", "KARAKA_SUFFIXES",
    "Sutra", "SutraEngine", "SubsumptionSutra", "SubsumptionEngine", "AmbiguityError",
    "to_prolog", "to_cypher",
]

__version__ = "0.2.0"
