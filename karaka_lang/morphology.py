"""
morphology.py -- real Paninian morphology via vidyut-prakriya.

This replaces the toy suffix table in parser.py with actual Ashtadhyayi
derivation. The approach is analysis-by-generation: given a lexicon of
nominal stems, generate every declined form (all vibhaktis, singular)
through vidyut-prakriya's rule engine once, and build a reverse map from
surface form back to (stem, vibhakti, karaka role). Every analyzed form
carries the full derivation history: the exact Ashtadhyayi sutra numbers
that produced it.

Scope notes, stated plainly:
- Analysis-by-generation only works for stems you registered. This is a
  closed-lexicon analyzer, which is the honest tradeoff for not needing
  vidyut's full downloadable kosha (dictionary) data. For a programming
  language, a closed lexicon is normal: it's a symbol table.
- Vibhakti (surface case) maps to karaka (semantic role) one-to-one here.
  Real Sanskrit does not always work that way: passives, verbs governing
  unusual cases, and upapada constructions break the neat mapping. The
  mapping used is the default, unmarked correspondence, and is documented
  as such. A production system would condition the mapping on the verb.
- vidyut is an optional dependency. Without it, karaka_lang falls back to
  the toy suffix parser and everything else still works.

Install with:  pip install -e ".[vidyut]"
"""

from __future__ import annotations
from dataclasses import dataclass, field

try:
    import vidyut.prakriya as _pk
    HAS_VIDYUT = True
except ImportError:
    HAS_VIDYUT = False

from .parser import Frame

# Default vibhakti -> karaka mapping (the unmarked correspondence).
# Sasthi (genitive) is not a karaka in Panini's own analysis; it marks
# relation (sambandha), and we keep that distinction in the name.
VIBHAKTI_TO_KARAKA = {
    "Prathama": "karta",        # nominative  -> agent
    "Dvitiya":  "karma",        # accusative  -> object
    "Trtiya":   "karana",       # instrumental-> instrument
    "Caturthi": "sampradana",   # dative      -> recipient
    "Panchami": "apadana",      # ablative    -> source
    "Sasthi":   "sambandha",    # genitive    -> relation (not a karaka proper)
    "Saptami":  "adhikarana",   # locative    -> locus
}


@dataclass
class Analysis:
    """One morphological analysis of a surface form."""
    surface: str
    stem: str
    vibhakti: str                 # e.g. "Trtiya"
    role: str                     # e.g. "karana"
    sutra_trace: list[str] = field(default_factory=list)  # Ashtadhyayi rule numbers

    def __repr__(self):
        return f"Analysis({self.surface}: {self.stem}+{self.vibhakti} -> {self.role})"


class VidyutResolver:
    """Closed-lexicon morphological analyzer backed by vidyut-prakriya.

    Register stems, then analyze surface forms. All declensions are
    generated through the real Ashtadhyayi rule engine, and each analysis
    keeps the sutra numbers that derived it.
    """

    def __init__(self):
        if not HAS_VIDYUT:
            raise ImportError(
                "vidyut is not installed. Install with: pip install vidyut\n"
                "(or pip install -e '.[vidyut]' from the repo root)"
            )
        self._v = _pk.Vyakarana()
        self._forms: dict[str, list[Analysis]] = {}
        self._stems: set[str] = set()

    def add_stem(self, stem: str, linga: str = "Pum") -> "VidyutResolver":
        """Register a nominal stem. Generates all seven vibhakti forms
        (singular) through vidyut-prakriya and indexes them for analysis.

        linga: "Pum" (masculine), "Stri" (feminine), or "Napumsaka" (neuter).
        """
        if stem in self._stems:
            return self
        self._stems.add(stem)
        linga_val = getattr(_pk.Linga, linga)
        prati = _pk.Pratipadika.basic(stem)
        for vib_name, role in VIBHAKTI_TO_KARAKA.items():
            vib = getattr(_pk.Vibhakti, vib_name)
            pada = _pk.Pada.Subanta(
                pratipadika=prati, linga=linga_val,
                vibhakti=vib, vacana=_pk.Vacana.Eka,
            )
            for prakriya in self._v.derive(pada):
                analysis = Analysis(
                    surface=prakriya.text,
                    stem=stem,
                    vibhakti=vib_name,
                    role=role,
                    sutra_trace=[step.code for step in prakriya.history],
                )
                self._forms.setdefault(prakriya.text, []).append(analysis)
        return self

    def add_stems(self, stems: dict[str, str]) -> "VidyutResolver":
        """Register several stems at once: {stem: linga}."""
        for stem, linga in stems.items():
            self.add_stem(stem, linga)
        return self

    def analyze(self, surface: str) -> list[Analysis]:
        """All analyses of a surface form. Empty list if unknown.
        A form can be genuinely ambiguous across stems or vibhaktis;
        the caller decides how to resolve (or reject) ambiguity."""
        return self._forms.get(surface, [])

    def parse(self, sentence: str, verb_forms: dict[str, str]) -> Frame:
        """Parse a sentence of declined words into a Frame.

        verb_forms maps surface verb forms to verb stems, e.g.
        {"gacchati": "gam"}. Verbs are looked up in this table; every
        other word must resolve through the registered lexicon.

        Raises ValueError on unknown words, ambiguous analyses, duplicate
        roles, or a verb count other than one -- ambiguity is surfaced,
        never silently resolved, consistent with the SubsumptionEngine's
        refusal to guess.
        """
        verb = None
        roles: dict[str, str] = {}
        for word in sentence.strip().split():
            w = word.strip(",.")
            if w in verb_forms:
                if verb is not None:
                    raise ValueError("Expected exactly one verb, found more")
                verb = verb_forms[w]
                continue
            analyses = self.analyze(w)
            if not analyses:
                raise ValueError(f"Unknown word (not in lexicon): {w!r}")
            distinct_roles = {a.role for a in analyses}
            if len(distinct_roles) > 1:
                raise ValueError(
                    f"Ambiguous analysis for {w!r}: could be any of "
                    f"{sorted(distinct_roles)}. Register a disambiguating "
                    f"context or use an unambiguous form."
                )
            a = analyses[0]
            if a.role in roles:
                raise ValueError(f"Duplicate karaka role '{a.role}' in frame")
            roles[a.role] = a.stem
        if verb is None:
            raise ValueError("Expected exactly one verb, found none")
        return Frame(verb=verb, roles=roles)

    def explain(self, surface: str) -> str:
        """Human-readable derivation trace for a form: which Ashtadhyayi
        sutras produced it."""
        analyses = self.analyze(surface)
        if not analyses:
            return f"{surface!r}: not in lexicon"
        lines = []
        for a in analyses:
            lines.append(
                f"{a.surface} = {a.stem} + {a.vibhakti} ({a.role}), "
                f"derived by sutras: {' -> '.join(a.sutra_trace)}"
            )
        return "\n".join(lines)
