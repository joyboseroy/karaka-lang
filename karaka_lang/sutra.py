"""
sutra.py -- Paninian-style ordered rewrite rules over Frames.

Two engines are provided:

- `SutraEngine` (v0): the original, honest-but-manual approach -- an
  explicit integer `specificity` set by the rule author. Kept because it
  still works and some rules genuinely don't reduce to condition
  subsumption. Its weakness (flagged independently by two reviewers of the
  position paper): manual integers don't compose. If two independently
  written rule sets both use `specificity=5`, combining them produces an
  arbitrary, silent ordering rather than a meaningful one.

- `SubsumptionEngine` (v1): specificity is *derived*, not assigned. Each
  rule declares `requires`, a set of conditions on the frame (e.g.
  {"verb=hara", "has:karana"}). Rule A is apavada (exception) to rule B
  iff A's requirements are a strict superset of B's -- A only fires in a
  narrower set of situations, so it's more specific, and applies later
  so it overrides. If two applicable rules' requirement sets are
  incomparable (neither is a subset of the other), that is a genuine
  structural ambiguity -- Panini's own commentarial tradition treated this
  as something requiring an explicit tie-breaking rule (a mechanism
  loosely related to how *asiddha* rule-ordering conflicts were resolved),
  not something a compiler should silently guess at, so
  `SubsumptionEngine.apply` raises `AmbiguityError` rather than picking an
  order.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, FrozenSet
from .parser import Frame


# ---------------------------------------------------------------------------
# v0: manual integer priority (kept for cases that don't reduce cleanly to
# condition subsumption, and for backward compatibility)
# ---------------------------------------------------------------------------

@dataclass
class Sutra:
    """A rewrite rule over Frames, ordered by an explicit priority integer.

    `specificity`: higher fires later and therefore wins on conflicting
    keys (utsarga/apavada: general rule first, exception overrides).
    """
    name: str
    condition: Callable[[Frame], bool]
    transform: Callable[[Frame], Frame]
    specificity: int = 0


class SutraEngine:
    def __init__(self):
        self.rules: list[Sutra] = []

    def add(self, sutra: Sutra) -> "SutraEngine":
        self.rules.append(sutra)
        return self

    def apply(self, frame: Frame) -> Frame:
        applicable = [r for r in self.rules if r.condition(frame)]
        applicable.sort(key=lambda r: r.specificity)
        for rule in applicable:
            frame = rule.transform(frame)
        return frame


# ---------------------------------------------------------------------------
# v1: subsumption-derived partial order
# ---------------------------------------------------------------------------

class AmbiguityError(Exception):
    """Raised when two applicable rules' requirement sets don't subsume one
    another -- there's no principled order between them, and the engine
    refuses to silently guess. Add a rule that requires the union of both
    conditions to break the tie explicitly, the way a Paninian commentator
    would add a rule to resolve an otherwise-undecided conflict."""


def _facts(frame: Frame) -> set[str]:
    """The set of atomic conditions this frame satisfies, used to check
    subsumption. A real system would extend this with sub-frame facts
    (recursing into nested `sambandha` frames); this toy version checks
    only the top-level verb and role presence, which is enough to
    demonstrate the mechanism."""
    facts = {f"verb={frame.verb}"}
    facts |= {f"has:{role}" for role in frame.roles}
    return facts


@dataclass
class SubsumptionSutra:
    """A rewrite rule whose applicability and specificity are both derived
    from `requires`, rather than an author-assigned priority number."""
    name: str
    requires: FrozenSet[str]
    transform: Callable[[Frame], Frame]

    def applies_to(self, frame: Frame) -> bool:
        return self.requires <= _facts(frame)


class SubsumptionEngine:
    def __init__(self):
        self.rules: list[SubsumptionSutra] = []

    def add(self, sutra: SubsumptionSutra) -> "SubsumptionEngine":
        self.rules.append(sutra)
        return self

    def apply(self, frame: Frame) -> Frame:
        applicable = [r for r in self.rules if r.applies_to(frame)]

        # Verify every pair of applicable rules is comparable (one's
        # requirements are a subset of the other's). If not, refuse to
        # guess -- see AmbiguityError docstring.
        for i, a in enumerate(applicable):
            for b in applicable[i + 1:]:
                if not (a.requires <= b.requires or b.requires <= a.requires):
                    raise AmbiguityError(
                        f"Rules '{a.name}' and '{b.name}' both apply to "
                        f"frame {frame!r} but neither's requirements "
                        f"subsume the other's ({sorted(a.requires)} vs "
                        f"{sorted(b.requires)}). Add a tie-breaking rule "
                        f"whose requirements are the union of both."
                    )

        # General (fewer requirements) first, specific (more requirements,
        # i.e. a strict superset -- apavada) last, so it overrides.
        applicable.sort(key=lambda r: len(r.requires))
        for rule in applicable:
            frame = rule.transform(frame)
        return frame
