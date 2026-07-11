"""
karaka_lang -- a Paninian kāraka-based calling convention for logic/relational
programming.

Arguments are bound to a predicate by grammatical role (agent, object,
instrument, recipient, source, locus) instead of by position, which makes
argument order irrelevant to meaning and fixes the arity/mode brittleness of
positional predicates in languages like Prolog.

Optional: with `pip install vidyut`, karaka_lang.morphology provides a real
Ashtadhyayi-backed morphological analyzer (VidyutResolver) in place of the
toy suffix table, with full sutra derivation traces per word.

See docs/DESIGN.md for architecture and docs/position-paper.md for the
research framing.
"""

from .parser import Token, Frame, tokenize, parse, KARAKA_SUFFIXES
from .sutra import Sutra, SutraEngine, SubsumptionSutra, SubsumptionEngine, AmbiguityError
from .codegen import (
    to_prolog, to_cypher,
    to_prolog_query, to_cypher_query,
    compile_frame, has_variables,
)
from .morphology import HAS_VIDYUT, VIBHAKTI_TO_KARAKA

__all__ = [
    "Token", "Frame", "tokenize", "parse", "KARAKA_SUFFIXES",
    "Sutra", "SutraEngine", "SubsumptionSutra", "SubsumptionEngine", "AmbiguityError",
    "to_prolog", "to_cypher", "to_prolog_query", "to_cypher_query",
    "compile_frame", "has_variables",
    "HAS_VIDYUT", "VIBHAKTI_TO_KARAKA",
]

if HAS_VIDYUT:
    from .morphology import VidyutResolver, Analysis
    __all__ += ["VidyutResolver", "Analysis"]

__version__ = "0.3.0"
