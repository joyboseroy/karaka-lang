"""
codegen.py -- compile a Frame to Prolog facts or a Cypher (FalkorDB) graph
write. Both are natural targets because a role-labeled Frame already is a
small labeled-edge structure around one event node.

Both functions recurse through nested Frames (roles whose value is itself
a Frame rather than a leaf string) -- see parser.Frame docstring on how
this removes the fixed six-role arity ceiling: a role can point to an
entire sub-event instead of a leaf entity.

QUERY MODE: a role whose value starts with "?" is a variable, not a
constant. A frame containing any variable compiles to a *query* (Cypher
MATCH / Prolog goal) instead of a write (Cypher MERGE / Prolog fact).
The same Frame type expresses both assertion and question; which one you
get is determined by whether anything is left open. This mirrors Prolog's
own duality between facts and goals, but with role-labeled rather than
positional arguments.
"""

from __future__ import annotations
import itertools
from .parser import Frame

_counter = itertools.count(1)


def _fresh_id(prefix: str = "s") -> str:
    return f"{prefix}{next(_counter)}"


def _is_var(value) -> bool:
    return isinstance(value, str) and value.startswith("?")


def has_variables(frame: Frame) -> bool:
    """True if any role (recursively) is a variable like '?who'."""
    for value in frame.roles.values():
        if isinstance(value, Frame):
            if has_variables(value):
                return True
        elif _is_var(value):
            return True
    return False


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


def to_prolog_query(frame: Frame, event_var: str = "E") -> str:
    """Compile a frame with variables into a Prolog goal (conjunctive
    query). '?who' becomes the Prolog variable Who. Constants stay
    constants. Nested frames get their own event variable."""
    goals: list[str] = [f"event({event_var}, {frame.verb})"]
    for role, arg in sorted(frame.roles.items(), key=lambda kv: kv[0]):
        if isinstance(arg, Frame):
            sub_var = f"E{next(_counter)}"
            goals.append(f"{role}({event_var}, {sub_var})")
            goals.append(to_prolog_query(arg, event_var=sub_var).rstrip("."))
        elif _is_var(arg):
            goals.append(f"{role}({event_var}, {arg[1:].capitalize()})")
        else:
            goals.append(f"{role}({event_var}, {arg})")
    return ", ".join(goals) + "."


def to_cypher_query(frame: Frame, node_name: str = "e") -> str:
    """Compile a frame with variables into a Cypher MATCH + RETURN.
    '?who' becomes a bound node variable returned by the query."""
    match_lines: list[str] = [f'MATCH ({node_name}:Event {{verb: "{frame.verb}"}})']
    returns: list[str] = []

    def walk(f: Frame, name: str):
        for role, arg in sorted(f.roles.items(), key=lambda kv: kv[0]):
            if isinstance(arg, Frame):
                sub = f"e{next(_counter)}"
                match_lines.append(
                    f'MATCH ({name})-[:{role.upper()}]->({sub}:Event {{verb: "{arg.verb}"}})'
                )
                walk(arg, sub)
            elif _is_var(arg):
                var = arg[1:]
                match_lines.append(f'MATCH ({name})-[:{role.upper()}]->({var}:Entity)')
                returns.append(f"{var}.name")
            else:
                match_lines.append(
                    f'MATCH ({name})-[:{role.upper()}]->(:Entity {{name: "{arg}"}})'
                )

    walk(frame, node_name)
    ret = "RETURN " + (", ".join(returns) if returns else node_name)
    return "\n".join(match_lines + [ret])


def compile_frame(frame: Frame, target: str = "cypher") -> str:
    """One entry point: assertion or query is decided by the frame itself.
    A frame with no variables compiles to a write; a frame with any
    '?variable' role compiles to a query."""
    if target == "cypher":
        return to_cypher_query(frame) if has_variables(frame) else to_cypher(frame)
    if target == "prolog":
        return to_prolog_query(frame) if has_variables(frame) else to_prolog(frame)
    raise ValueError(f"Unknown target: {target!r} (use 'cypher' or 'prolog')")
