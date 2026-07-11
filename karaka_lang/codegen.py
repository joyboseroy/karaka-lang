"""
codegen.py -- compile a Frame to Prolog facts or a Cypher (FalkorDB) graph
write. Both are natural targets because a role-labeled Frame already is a
small labeled-edge structure around one event node.

Both functions recurse through nested Frames (roles whose value is itself
a Frame rather than a leaf string) -- see parser.Frame docstring on how
this removes the fixed six-role arity ceiling: a role can point to an
entire sub-event instead of a leaf entity.
"""

from __future__ import annotations
import itertools
from .parser import Frame

_counter = itertools.count(1)


def _fresh_id(prefix: str = "s") -> str:
    return f"{prefix}{next(_counter)}"


def to_prolog(frame: Frame, event_id: str | None = None) -> str:
    """Compile to normalized binary predicates (event + role edges) rather
    than a single positional term. Nested Frames get their own event id and
    an extra edge linking parent event to sub-event via the role name."""
    eid = event_id or _fresh_id()
    lines = [f"event({eid}, {frame.verb})."]
    for role, arg in sorted(frame.roles.items(), key=lambda kv: kv[0]):
        if isinstance(arg, Frame):
            sub_id = _fresh_id()
            lines.append(f"{role}({eid}, {sub_id}).")
            lines.append(to_prolog(arg, event_id=sub_id))
        else:
            lines.append(f"{role}({eid}, {arg}).")
    return "\n".join(lines)


def to_cypher(frame: Frame, node_name: str | None = None) -> str:
    """Compile to Cypher MERGE statements. Nested Frames become their own
    :Event node, linked from the parent by a role-labeled edge, instead of
    an :Entity leaf node."""
    name = node_name or "e"
    lines = [f'MERGE ({name}:Event {{verb: "{frame.verb}"}})']
    for role, arg in sorted(frame.roles.items(), key=lambda kv: kv[0]):
        if isinstance(arg, Frame):
            sub_name = _fresh_id("n")
            lines.append(to_cypher(arg, node_name=sub_name))
            lines.append(f'MERGE ({name})-[:{role.upper()}]->({sub_name})')
        else:
            leaf_name = f"n_{arg}"
            lines.append(
                f'MERGE ({leaf_name}:Entity {{name: "{arg}"}}) '
                f'MERGE ({name})-[:{role.upper()}]->({leaf_name})'
            )
    return "\n".join(lines)
