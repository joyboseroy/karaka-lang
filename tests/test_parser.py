import re
import pytest
from karaka_lang import (
    parse, Frame, Sutra, SutraEngine,
    SubsumptionSutra, SubsumptionEngine, AmbiguityError,
    to_prolog, to_cypher,
)


def test_order_invariance():
    variants = [
        "robotah pakasthanam gacchati",
        "gacchati robotah pakasthanam",
        "pakasthanam robotah gacchati",
    ]
    frames = [parse(v) for v in variants]
    assert all(f == frames[0] for f in frames)
    assert frames[0].verb == "gaccha"
    assert frames[0].roles == {"karta": "robot", "karma": "pakasthan"}


def test_duplicate_role_raises():
    with pytest.raises(ValueError):
        parse("robotah devah gacchati")  # two nominative (karta) args


def test_missing_verb_raises():
    with pytest.raises(ValueError):
        parse("robotah pakasthanam")


def test_instrument_and_source_roles():
    f = parse("manah ksetraya jalena jalasayat harati")
    assert f.verb == "hara"
    assert f.roles["karta"] == "man"
    assert f.roles["sampradana"] == "ksetr"
    assert f.roles["karana"] == "jal"
    assert f.roles["apadana"] == "jalasay"


def test_sutra_apavada_overrides_utsarga():
    frame = parse("manah ksetraya jalena harati")
    engine = SutraEngine()
    engine.add(Sutra(
        name="default-liability",
        condition=lambda f: f.verb == "hara",
        transform=lambda f: Frame(f.verb, {**f.roles, "liability": "strict"}),
        specificity=0,
    ))
    engine.add(Sutra(
        name="instrument-liability-exception",
        condition=lambda f: f.verb == "hara" and "karana" in f.roles,
        transform=lambda f: Frame(f.verb, {**f.roles, "liability": "instrument-based"}),
        specificity=1,
    ))
    resolved = engine.apply(frame)
    assert resolved.roles["liability"] == "instrument-based"


def test_sutra_utsarga_alone_applies_when_no_exception_matches():
    frame = parse("manah ksetraya harati")  # no instrument
    engine = SutraEngine()
    engine.add(Sutra(
        name="default-liability",
        condition=lambda f: f.verb == "hara",
        transform=lambda f: Frame(f.verb, {**f.roles, "liability": "strict"}),
        specificity=0,
    ))
    engine.add(Sutra(
        name="instrument-liability-exception",
        condition=lambda f: f.verb == "hara" and "karana" in f.roles,
        transform=lambda f: Frame(f.verb, {**f.roles, "liability": "instrument-based"}),
        specificity=1,
    ))
    resolved = engine.apply(frame)
    assert resolved.roles["liability"] == "strict"


def test_codegen_prolog():
    f = parse("robotah pakasthanam gacchati")
    out = to_prolog(f, event_id="e1")
    assert "event(e1, gaccha)." in out
    assert "karta(e1, robot)." in out
    assert "karma(e1, pakasthan)." in out


def test_codegen_cypher():
    f = parse("robotah pakasthanam gacchati")
    out = to_cypher(f)
    assert 'MERGE (e:Event {verb: "gaccha"})' in out
    assert "[:KARTA]->(n_robot)" in out
    assert "[:KARMA]->(n_pakasthan)" in out


# --- arity fix: nested Sambandha frames -------------------------------

def test_nested_frame_extends_arity_beyond_six_roles():
    # instrument is itself an event (a flood caused by rainfall), nested
    # under karana instead of being a flat leaf -- this is how arity is
    # extended without adding more kāraka roles.
    rainfall_event = Frame("varsa", {"karta": "megh"})  # "cloud rains"
    flood_event = Frame("hara", {
        "karta": "man",
        "sampradana": "field",
        "karana": rainfall_event,   # nested, not a leaf string
        "apadana": "reservoir",
    })
    assert isinstance(flood_event.roles["karana"], Frame)
    assert flood_event.roles["karana"].verb == "varsa"


def test_codegen_prolog_recurses_into_nested_frames():
    rainfall_event = Frame("varsa", {"karta": "megh"})
    flood_event = Frame("hara", {"karta": "man", "karana": rainfall_event})
    out = to_prolog(flood_event, event_id="e1")
    assert "event(e1, hara)." in out
    assert "karta(e1, man)." in out
    m = re.search(r"karana\(e1, (\w+)\)\.", out)
    assert m, f"expected a karana(e1, <sub_id>) edge in:\n{out}"
    sub_id = m.group(1)
    assert f"event({sub_id}, varsa)." in out
    assert f"karta({sub_id}, megh)." in out


def test_codegen_cypher_recurses_into_nested_frames():
    rainfall_event = Frame("varsa", {"karta": "megh"})
    flood_event = Frame("hara", {"karta": "man", "karana": rainfall_event})
    out = to_cypher(flood_event)
    assert 'MERGE (e:Event {verb: "hara"})' in out
    assert '{verb: "varsa"}' in out
    assert "[:KARANA]->(n" in out            # edge to sub-event node


# --- rule ordering fix: subsumption engine ------------------------------

def test_subsumption_engine_apavada_overrides_utsarga():
    frame = parse("manah ksetraya jalena harati")
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
    resolved = engine.apply(frame)
    assert resolved.roles["liability"] == "instrument-based"


def test_subsumption_engine_general_rule_alone_when_exception_doesnt_match():
    frame = parse("manah ksetraya harati")  # no instrument
    engine = SubsumptionEngine()
    engine.add(SubsumptionSutra(
        name="default-liability",
        requires=frozenset({"verb=hara"}),
        transform=lambda f: Frame(f.verb, {**f.roles, "liability": "strict"}),
    ))
    engine.add(SubsumptionSutra(
        name="instrument-liability-exception",
        requires=frozenset({"verb=hara", "has:karana"}),
        transform=lambda f: Frame(f.verb, {**f.roles, "liability": "instrument-based"}),
    ))
    resolved = engine.apply(frame)
    assert resolved.roles["liability"] == "strict"


def test_subsumption_engine_raises_on_genuine_ambiguity():
    # Two rules whose requirement sets are incomparable (neither subsumes
    # the other) both matching the same frame -- the engine must refuse to
    # silently pick a winner.
    frame = parse("manah ksetraya jalena harati")
    engine = SubsumptionEngine()
    engine.add(SubsumptionSutra(
        name="rule-a",
        requires=frozenset({"verb=hara", "has:karana"}),
        transform=lambda f: Frame(f.verb, {**f.roles, "tag": "a"}),
    ))
    engine.add(SubsumptionSutra(
        name="rule-b",
        requires=frozenset({"verb=hara", "has:sampradana"}),  # incomparable to rule-a
        transform=lambda f: Frame(f.verb, {**f.roles, "tag": "b"}),
    ))
    with pytest.raises(AmbiguityError):
        engine.apply(frame)

