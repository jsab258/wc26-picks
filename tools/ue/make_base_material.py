"""Make the Unreal base material for the D1b vignette, from a script, in CI.

    UnrealEditor-Cmd.exe LedgerProbe.uproject -run=pythonscript \
        -script="tools/ue/make_base_material.py" -unattended -nopause -nosplash
    python3 tools/ue/make_base_material.py --selftest   # runs without Unreal

WHY IT EXISTS AT ALL, which is the whole of D1 measurement (a).

Unreal cannot build a material at runtime: a material is compiled shader
code, the shader compiler is editor-only, and a packaged game can only make
INSTANCES of materials that already exist as assets. So Phase C needs one
binary asset. The project's standing rule is that no human opens the editor
and no human hand-makes a uasset, and Jafar's decision rule for D1 (second
amendment, 2 September) says Unreal fails measurement (a) if it turns out to
depend on hand edits. This script is the answer to that question in
executable form: the asset is a BUILD PRODUCT, made by a script that runs in
the cook step and is committed like any other build output.

If this script cannot make the material, that IS the D1 answer and it must be
reported as one rather than worked around by opening the editor.

WHAT IT MAKES. One material, /Game/Ledger/M_LedgerSurface, with three texture
parameters and two scalar parameters:

    BaseColorMap   -> Base Color     the pack's <surface>.jpg
    NormalMap      -> Normal         the pack's <surface>_n.jpg
    RoughnessMap   -> Roughness      the pack's <surface>_r.jpg
    TilingU/TilingV                  how many times the maps repeat

THE PARAMETER NAMES ARE A CONTRACT WITH C++ that nothing at runtime can
check: a dynamic instance asked for a parameter the material does not have
sets nothing, returns nothing and logs nothing, and the frame comes back
untextured with every count green. The names live in
ue-probe/Source/LedgerProbe/Public/SurfaceBind.h, which is the tested layer,
and --selftest reads them out of that file and compares them to the names
below. That is the one half of this script that can be run in the container
that writes it, so it is the half that is run before every dispatch.

EVERY WIRING STEP IS INDIVIDUALLY GUARDED AND COUNTED. A material with a
base colour and no normal map is worth having; a script that dies halfway
and saves nothing is not. What landed is written to ue-material.txt beside
the project as key=value, because a log tail is not an evidence channel in
this project and a committed file is.

WHAT RUN 19 PRINTED, AND WHY THIS FILE NOW DECIDES ITS OWN VERDICT.
Run 19 shipped `materialScriptExit=1` beside `materialStatus=MADE
materialParamsMade=3/3 materialConnections=12/14`, and both cannot be the
answer. Two separate faults produced that pair:

  1. THE EXIT CODE WAS NOT THIS SCRIPT'S. main() returns 0 or 2 and never 1,
     so a 1 cannot have come from here: the workflow was reading the exit
     code of UnrealEditor-Cmd.exe, which also shuts an editor down, and
     calling it the script's. The verdict this file is sure of is now
     WRITTEN INTO THE EVIDENCE FILE as materialScriptReturn, and the
     process's own code is named for what it is by the step that reads it.
     sys.exit is not called when this runs inside the editor either: raising
     SystemExit through an embedded interpreter is a plausible way to turn a
     successful script into a non-zero process, and nothing is gained by it.

  2. MADE WAS OVERCLAIMING. It asked only whether the asset saved and whether
     three parameters exist, so twelve of fourteen connections wired read as
     a clean pass; the two that refused were TexCoord into both component
     masks, which is the head of the UV chain every sampler hangs off. A
     material whose UVs are unconnected is not a made material. The status
     now needs every connection the script asked for, and the return code is
     a function OF THE STATUS, so no run can print a failure beside MADE
     again.

THE STATUS AND THE RETURN CODE ARE COMPUTED BY PURE FUNCTIONS AT THE TOP OF
THIS FILE and exercised by --selftest, which runs in the container that
writes them. Everything that needs Unreal supplies numbers; nothing that
needs Unreal decides what the numbers mean.

WHAT RUN 20 LANDED, AND WHY THE UV HEAD IS NOW SWEPT RATHER THAN NAMED.
Run 20 wired the same 12 of 14 as run 19 and refused the same two, verbatim:
texcoord-to-maskU-refused/texcoord-to-maskV-refused. Those two are the head
of the UV chain all three samplers hang off, so every sampler read one texel
and 563 correctly textured pieces rendered as one flat colour each.

Both refusals name a pin. connect_material_expressions takes the output pin
name and the input pin name as STRINGS and answers false when either names a
pin the expression does not have: no exception, no log line, one false. The
two refused calls are the only two in this script that ask for an input named
Input, and they are also the only two whose source is the TextureCoordinate
expression, so the fault is one of those two names. WHICH ONE IS NOT
ESTABLISHED HERE AND COULD NOT BE: there is no engine, no unreal module and
no engine source in this container, and Epic's Python API reference is not
reachable from it (the agent proxy answers 403 CONNECT for dev.epicgames.com,
recorded in its own status). A guess would cost a 25 minute round trip per
wrong name.

So the name is MEASURED ON THE RUNNER instead of asserted here. Each head
connection is asked for under UV_PIN_CANDIDATES, most likely pair first,
until the editor accepts one, and the pair that answered is printed as
materialUvHeadVia. The sweep contains the exact pair runs 19 and 20 used, so
it cannot wire less than they did; it counts ONE connection however many
names it tries, so the denominator stays 14; and the graph is read back
afterwards, because the editor's boolean is not the only witness worth
having.
"""

import os
import sys

# THE CONTRACT. Read by --selftest out of the tested header, never retyped
# there. Order is base colour, normal, roughness, matching MapParam().
TEXTURE_PARAMS = ["BaseColorMap", "NormalMap", "RoughnessMap"]
SCALAR_PARAMS = ["TilingU", "TilingV"]

# THE ONE PAIR OF PIN NAMES THIS SCRIPT CANNOT ESTABLISH FROM HERE.
# Each entry is (output pin name on the TextureCoordinate, input pin name on
# the ComponentMask), ordered most likely first. The ordering is a hypothesis;
# only the run can say which pair is right, and it prints the one that was.
#   1. empty into empty. Every connection that DID wire in runs 19 and 20
#      passed "" as its output name, so "" is known to match an unnamed pin in
#      this engine version, and the mask's single input draws unlabelled.
#   2. empty into Input. Exactly what runs 19 and 20 asked for and were
#      refused. Kept FIRST among the named ones so the sweep can never wire
#      less than they did and so the run says out loud whether that name was
#      the fault.
#   3. the FName None spelled out, for a library comparing ToString() output
#      rather than FName against FName.
#   4. the two words the node's coordinate input is described by elsewhere.
#   5. the same sweep with the OUTPUT named, because the other live hypothesis
#      is that the refusal is on the TextureCoordinate side: these are the
#      only two calls in this script whose source is one.
UV_PIN_CANDIDATES = [
    ("", ""),
    ("", "Input"),
    ("", "None"),
    ("", "Coordinates"),
    ("", "UVs"),
    ("None", ""),
    ("None", "Input"),
    ("UV", ""),
    ("UVs", ""),
]

# The two head connections, in the order main() makes them. Used only to
# label the verdict value when the two masks answer differently.
UV_HEAD_NAMES = ["maskU", "maskV"]

PACKAGE = "/Game/Ledger"
ASSET = "M_LedgerSurface"
ASSET_PATH = PACKAGE + "/" + ASSET

# DEFAULT TEXTURES ARE TRIED IN ORDER AND THE ONE THAT ANSWERED IS NAMED. A
# texture parameter with no default can fail to compile, and an engine asset
# path that moved between versions is exactly the kind of assumption that
# costs a 25 minute round trip to discover.
COLOUR_DEFAULTS = [
    "/Engine/EngineResources/DefaultTexture",
    "/Engine/EngineResources/WhiteSquareTexture",
    "/Engine/EngineMaterials/DefaultDiffuse",
]
NORMAL_DEFAULTS = [
    "/Engine/EngineMaterials/DefaultNormal",
    "/Engine/EngineResources/DefaultTextureNormal",
]


# ---- the verdict, decided by pure functions the container can run --------
#
# EVERY NUMBER BELOW COMES FROM THE EDITOR AND EVERY JUDGEMENT ABOUT IT
# HAPPENS HERE, for the standing reason: a formatter or a status rule written
# where the tests cannot reach it ships unrun, and an unrun rule printing a
# plausible word is the silent-instrument failure this project keeps paying
# for. --selftest exercises all three of these before any dispatch.

STATUS_MADE = "MADE"
STATUS_PARTIAL = "PARTIAL"
STATUS_NOT_SAVED = "NOT-SAVED"


def material_status(saved, params_made, params_asked, wired, asked):
    """One word for what this run of the script achieved.

    MADE needs all three of: the asset saved to disk, every texture parameter
    the C++ contract names, and every connection the script asked the editor
    to make. The third clause is new. Run 19 wired 12 of 14 and still said
    MADE, and the two that refused were TexCoord into the component masks:
    the head of the UV chain that all three samplers hang off, so every
    sampler in that material reads one texel. A material whose UV chain is
    unconnected has not been made.

    PARTIAL is a saved asset that fell short of one of those, which is worth
    keeping and is not a pass. NOT-SAVED is nothing on disk at all.
    """
    if not saved:
        return STATUS_NOT_SAVED
    if params_made < params_asked:
        return STATUS_PARTIAL
    if asked <= 0 or wired < asked:
        return STATUS_PARTIAL
    return STATUS_MADE


def material_return(status):
    """The script's own return code, a FUNCTION of the status and never a
    second opinion about it. Two numbers derived from one variable are one
    number twice, and that is the point here: the pair that made run 19
    unreadable cannot be printed again."""
    return 0 if status == STATUS_MADE else 2


class Wiring(object):
    """The connection tally, kept in the half of this file the container can
    run because a count that decides a verdict must not ship unrun.

    asked counts CONNECTIONS ASKED FOR and never candidate pin names: a head
    connection swept over nine candidate names is one connection, so the
    denominator stays 14 whatever the sweep costs. wired counts the ones the
    editor accepted. materialStatus reads MADE only when the two are equal,
    which is the 3 September rule and is not relaxed here.
    """

    def __init__(self):
        self.wired = 0
        self.asked = 0
        self.notes = []

    def record(self, ok, note):
        """One connection, counted once. note is the token appended when it
        did not land; nothing is appended when it did, because the notes field
        is a list of faults and a note per success would bury them."""
        self.asked += 1
        if ok:
            self.wired += 1
        elif note:
            self.notes.append(note)
        return ok


def pin_token(out_name, in_name):
    """One candidate pair, as a value with no spaces and no second equals.
    The word empty stands for the empty string, which is a real pin name in
    this API and would otherwise print as nothing at all and read as a bug."""
    return "out.%s..in.%s" % (out_name or "empty", in_name or "empty")


def connect_by_candidates(try_connect, candidates):
    """Ask the editor for one connection under each candidate pair of pin
    names until a pair answers, and report WHICH pair did.

    try_connect(out_name, in_name) -> bool is the editor's opinion and the
    only part of this that needs Unreal. The search, the count and the token
    are decided here, where --selftest can run them, and a candidate that
    RAISES is a candidate that did not answer rather than the end of the
    sweep: an API that rejects an unknown pin name by throwing would
    otherwise abandon the eight names after it.

    Returns (ok, tried, out_name, in_name). tried is how many pairs were asked
    for, so it is 1 when the first pair answered and len(candidates) when none
    did, and the names are None when none did.
    """
    tried = 0
    for out_name, in_name in candidates:
        tried += 1
        try:
            ok = bool(try_connect(out_name, in_name))
        except Exception:
            ok = False
        if ok:
            return True, tried, out_name, in_name
    return False, tried, None, None


def uv_head_note(what, candidates_total):
    """The token appended when a head connection did not land.

    It keeps the exact string runs 19 and 20 printed as a PREFIX, so a grep
    for texcoord-to-maskU-refused across the verdict files still finds the
    next failure, and adds what the new attempt cost. Formatted here rather
    than in main() because a string built where the tests cannot reach it
    ships unrun.
    """
    return "%s-refused-after-%d-candidates" % (what, candidates_total)


def uv_head_fields(results, candidates_total):
    """The three values the UV head ships on the verdict line.

    results is one record per head connection, in the order main() makes them:

        (ok, via, tried, readback)

    via is the token for HOW it was made, tried is how many candidate pairs
    were asked for, and readback is True, False or None for the graph read
    back afterwards, where None means the editor would not answer and is not
    the same fact as no.

    Returns (via, triedAtWorst, readback), all three free of spaces. The
    second is a max and says so in its key. A run holding no records prints
    the words nothing measured rather than a clean-looking zero.
    """
    if not results:
        return ("nothing-measured",
                "nothing-measured/%d" % candidates_total,
                "nothing-measured")
    vias = [r[1] for r in results]
    if len(set(vias)) == 1:
        via = ("both.%s" % vias[0]) if len(results) > 1 else vias[0]
    else:
        named = []
        for i, v in enumerate(vias):
            head = UV_HEAD_NAMES[i] if i < len(UV_HEAD_NAMES) else "head%d" % i
            named.append("%s.%s" % (head, v))
        via = "/".join(named)
    tried = max(r[2] for r in results)
    yes = len([r for r in results if r[3] is True])
    unreadable = len([r for r in results if r[3] is None])
    return (via,
            "%d/%d" % (tried, candidates_total),
            "%d/%d..unreadable%d" % (yes, len(results), unreadable))


def material_line(status, params_made, params_asked, wired, asked, existed,
                  colour_from, normal_from, defaults_bound, defaults_asked,
                  saved, notes, uv_via, uv_tried, uv_readback):
    """The one line the workflow copies into the build verdict.

    No spaces inside any value: every reader of these files splits on
    whitespace. Every count ships its denominator, including the engine
    default textures, which run 19 reported as `none-of-2-candidates` with no
    total beside it.

    The three UV head values are readings, not verdicts, and nothing branches
    on them:
      materialUvHeadVia          which pair of pin names the editor accepted,
                                 or none-of-N-candidates, for both masks or
                                 named per mask when the two differ.
      materialUvHeadTriedAtWorst candidate pairs asked for, AT WORST of the
                                 two head connections, over the number
                                 available. 1/9 means the first pair answered.
      materialUvHeadReadback     head connections whose input reads back as
                                 the TexCoord node, over the head connections
                                 made, with the count the editor would not
                                 answer for carried beside it rather than
                                 folded into the no.
    """
    return ("materialStatus=%s materialScriptReturn=%d materialPath=%s "
            "materialExistedBefore=%s materialParams=%s materialParamsMade=%d/%d "
            "materialScalars=%s materialConnections=%d/%d "
            "materialUvHeadVia=%s materialUvHeadTriedAtWorst=%s "
            "materialUvHeadReadback=%s "
            "materialColourDefault=%s materialNormalDefault=%s "
            "materialDefaultsBound=%d/%d materialSaved=%s "
            "materialVerdictIs=materialScriptReturn/not-the-editor-process-exit "
            "materialNote=%s"
            % (status, material_return(status), ASSET_PATH,
               "yes" if existed else "no",
               "/".join(TEXTURE_PARAMS), params_made, params_asked,
               "/".join(SCALAR_PARAMS), wired, asked,
               uv_via, uv_tried, uv_readback,
               str(colour_from).replace(" ", "~"),
               str(normal_from).replace(" ", "~"),
               defaults_bound, defaults_asked,
               "yes" if saved else "NO",
               "/".join(notes) if notes else "none"))


def selftest():
    """The name contract, checked against the tested header. Accepting case
    first: the live SurfaceBind.h is the accepting fixture, as the project's
    rule for tools that check the project itself requires."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(here))
    header = os.path.join(root, "ue-probe", "Source", "LedgerProbe",
                          "Public", "SurfaceBind.h")
    checks = 0
    bad = []
    if not os.path.exists(header):
        print("make_base_material --selftest: NOTHING MEASURED, no %s" % header)
        return 1
    text = open(header, "r", encoding="utf-8").read()
    # The header states the parameter names in MapParam(); read them rather
    # than trusting that the two lists were kept in step by hand.
    at = text.find("const char* P[3] =")
    if at < 0:
        print("make_base_material --selftest: NOTHING MEASURED, "
              "SurfaceBind.h has no MapParam list to read")
        return 1
    line = text[at:text.find(";", at)]
    names = [p.strip().strip('"') for p in
             line[line.find("{") + 1:line.find("}")].split(",")]
    checks += 1
    if names != TEXTURE_PARAMS:
        bad.append("the header asks for %s and this script makes %s"
                   % (names, TEXTURE_PARAMS))
    # And the scalars, which the binder sets per piece. They are set in the
    # module rather than named in the header, so the whole source tree is the
    # haystack: the contract is "some C++ site sets this", not "this file
    # mentions it".
    src = os.path.join(root, "ue-probe", "Source")
    blob = ""
    files = 0
    for base, _dirs, found in os.walk(src):
        for n in found:
            if n.endswith((".cpp", ".h")):
                files += 1
                blob += open(os.path.join(base, n), "r", encoding="utf-8").read()
    for s in SCALAR_PARAMS:
        checks += 1
        if ('"%s"' % s) not in blob:
            bad.append("no C++ site in the %d source file(s) under ue-probe/Source "
                       "sets the scalar parameter %s" % (files, s))
    # ---- the verdict rule, both ways round, ACCEPTING CASE FIRST ---------
    # A guard shipped without a run in which it passes is a ratchet, and one
    # shipped without a run in which it fires is a claim. Both are here, and
    # the rejecting case is run 19's own numbers.
    cases = [
        # (saved, made, asked_params, wired, asked, status, return)
        (True, 3, 3, 14, 14, STATUS_MADE, 0),
        (True, 3, 3, 12, 14, STATUS_PARTIAL, 2),   # run 19, exactly
        (True, 2, 3, 14, 14, STATUS_PARTIAL, 2),
        (True, 3, 3, 0, 0, STATUS_PARTIAL, 2),     # nothing asked is not a pass
        (False, 3, 3, 14, 14, STATUS_NOT_SAVED, 2),
    ]
    for saved, made, pasked, wired, casked, want, want_code in cases:
        checks += 1
        got = material_status(saved, made, pasked, wired, casked)
        code = material_return(got)
        if got != want or code != want_code:
            bad.append("status(saved=%s made=%d/%d wired=%d/%d) gave %s/%d "
                       "and should give %s/%d"
                       % (saved, made, pasked, wired, casked, got, code,
                          want, want_code))
    # ---- THE UV HEAD, WHICH IS THE THING THAT DID NOT WIRE --------------
    # None of this can open Unreal, and that is the point: what CAN be run
    # here is the search, the counting and the tokens, so an engine faked in
    # nine lines below stands in for the editor's yes and no. The one thing
    # left unrun is which pin name the real editor accepts, and the run
    # prints that as materialUvHeadVia rather than this file asserting it.

    def accept_only(pair):
        return lambda o, i: (o, i) == pair

    def accept_nothing(o, i):
        return False

    def throw_unless(pair):
        def f(o, i):
            if (o, i) != pair:
                raise RuntimeError("an engine that rejects an unknown pin "
                                   "name by throwing rather than by no")
            return True
        return f

    ncand = len(UV_PIN_CANDIDATES)
    checks += 1
    if ncand < 2 or len(set(UV_PIN_CANDIDATES)) != ncand:
        bad.append("the %d UV candidate pair(s) must be at least 2 and all "
                   "distinct: %s" % (ncand, UV_PIN_CANDIDATES))
    checks += 1
    dirty = [p for p in UV_PIN_CANDIDATES
             if any((" " in n) or ("=" in n) for n in p)]
    if dirty:
        bad.append("a candidate pin name carries a space or an equals and "
                   "would break the verdict line: %s" % dirty)
    checks += 1
    if ("", "Input") not in UV_PIN_CANDIDATES:
        bad.append("the pair runs 19 and 20 asked for is not in the sweep, so "
                   "this change could wire FEWER connections than they did")
    checks += 1
    if pin_token("", "") != "out.empty..in.empty" or \
            pin_token("", "Input") != "out.empty..in.Input" or \
            " " in pin_token("", ""):
        bad.append("pin_token does not name the empty pin or carries a space: "
                   "%s %s" % (pin_token("", ""), pin_token("", "Input")))
    # ACCEPTING CASE FIRST: an engine that takes the pair this sweep tries
    # first answers on the first ask and is named for it.
    checks += 1
    got = connect_by_candidates(accept_only(UV_PIN_CANDIDATES[0]),
                                UV_PIN_CANDIDATES)
    if got != (True, 1, UV_PIN_CANDIDATES[0][0], UV_PIN_CANDIDATES[0][1]):
        bad.append("the sweep did not take the first candidate from an engine "
                   "that accepts only it: %s" % (got,))
    # AND THE ONE THE OLD CODE USED, which is the guarantee that this change
    # cannot wire less than run 20 did: an engine behaving exactly as run 20's
    # would have to for "Input" to be right still wires, at candidate 2 of 9.
    checks += 1
    old_pair = ("", "Input")
    ok, tried, o, i = connect_by_candidates(accept_only(old_pair),
                                            UV_PIN_CANDIDATES)
    if not ok or (o, i) != old_pair or tried != UV_PIN_CANDIDATES.index(old_pair) + 1:
        bad.append("an engine accepting only the name runs 19 and 20 used is "
                   "no longer wired by the sweep: ok=%s tried=%d pair=%s"
                   % (ok, tried, (o, i)))
    # A CANDIDATE THAT RAISES IS A NO AND NOT THE END OF THE SWEEP. Caught
    # here rather than left to propagate, so that losing the guard prints a
    # named failure and not a traceback from inside the fixture.
    checks += 1
    try:
        ok, tried, o, i = connect_by_candidates(
            throw_unless(UV_PIN_CANDIDATES[-1]), UV_PIN_CANDIDATES)
    except Exception as e:
        ok, tried, o, i = False, -1, "raised", str(e)[:60].replace(" ", "~")
    if not ok or (o, i) != UV_PIN_CANDIDATES[-1] or tried != ncand:
        bad.append("a throwing candidate ended the sweep instead of counting "
                   "as a no: ok=%s tried=%s pair=%s" % (ok, tried, (o, i)))
    # REJECTING CASE: nothing answers, and the value says so with its total.
    checks += 1
    ok, tried, o, i = connect_by_candidates(accept_nothing, UV_PIN_CANDIDATES)
    if ok or tried != ncand or o is not None or i is not None:
        bad.append("the sweep claimed a connection from an engine that "
                   "refuses every name: ok=%s tried=%d pair=%s"
                   % (ok, tried, (o, i)))
    # THE DENOMINATOR. A head connection swept over nine names is ONE
    # connection asked for, or 14 stops being the number runs 19 and 20
    # printed and the fraction stops being comparable across runs.
    good = Wiring()
    for head in UV_HEAD_NAMES:
        swept = connect_by_candidates(accept_only(UV_PIN_CANDIDATES[0]),
                                      UV_PIN_CANDIDATES)
        good.record(swept[0], uv_head_note("texcoord-to-%s" % head, ncand))
    for _ in range(12):
        good.record(True, "a-note-for-a-connection-that-landed")
    checks += 1
    if (good.wired, good.asked, good.notes) != (14, 14, []):
        bad.append("a swept head connection did not count as one connection: "
                   "wired=%d asked=%d notes=%s"
                   % (good.wired, good.asked, good.notes))
    checks += 1
    if material_status(True, 3, 3, good.wired, good.asked) != STATUS_MADE:
        bad.append("14 of 14 wired with 3 of 3 parameters and a saved asset "
                   "does not read MADE, so the acceptance can never be met")
    # AND RUN 19 AND 20's OWN SHAPE, rebuilt through the same tally: two heads
    # refused by every name, twelve others landing, 12 of 14 and PARTIAL.
    run19 = Wiring()
    for head in UV_HEAD_NAMES:
        swept = connect_by_candidates(accept_nothing, UV_PIN_CANDIDATES)
        run19.record(swept[0], uv_head_note("texcoord-to-%s" % head, ncand))
    for _ in range(12):
        run19.record(True, None)
    checks += 1
    if (run19.wired, run19.asked) != (12, 14) or \
            material_status(True, 3, 3, run19.wired, run19.asked) != STATUS_PARTIAL:
        bad.append("the run 19 shape no longer reproduces as 12/14 PARTIAL: "
                   "wired=%d asked=%d" % (run19.wired, run19.asked))
    checks += 1
    if not all(n.startswith("texcoord-to-%s-refused" % h)
               for n, h in zip(run19.notes, UV_HEAD_NAMES)):
        bad.append("the refusal notes no longer carry the token runs 19 and "
                   "20 printed as a prefix, so a grep for it would miss the "
                   "next failure: %s" % run19.notes)
    # ---- and the three values the head ships, all four shapes ------------
    win = pin_token("", "")
    checks += 1
    fields = uv_head_fields([(True, win, 1, True), (True, win, 1, True)], ncand)
    if fields != ("both." + win, "1/%d" % ncand, "2/2..unreadable0"):
        bad.append("two heads made the same way do not read as one value: %s"
                   % (fields,))
    checks += 1
    other = "none-of-%d-candidates..then.property-write-took" % ncand
    fields = uv_head_fields([(True, win, 1, True), (True, other, ncand, False)],
                            ncand)
    if fields != ("maskU.%s/maskV.%s" % (win, other),
                  "%d/%d" % (ncand, ncand), "1/2..unreadable0"):
        bad.append("two heads made different ways are not named apart: %s"
                   % (fields,))
    checks += 1
    fields = uv_head_fields([(True, win, 1, None), (True, win, 2, None)], ncand)
    if fields != ("both." + win, "2/%d" % ncand, "0/2..unreadable2"):
        bad.append("a readback the editor would not answer is being counted "
                   "as a no, or the tried value is not the worst of the two: "
                   "%s" % (fields,))
    checks += 1
    fields = uv_head_fields([], ncand)
    if fields[0] != "nothing-measured" or "nothing-measured" not in fields[1] \
            or fields[2] != "nothing-measured":
        bad.append("a head that never ran does not print the words nothing "
                   "measured: %s" % (fields,))
    # AND THE LINE ITSELF, because an unrun formatter printing a plausible
    # string is the fault this file exists on the tested side to avoid. The
    # rule every reader of these files depends on: one equals per token and
    # no spaces inside a value.
    line = material_line(STATUS_PARTIAL, 3, 3, 12, 14, False,
                         "/Engine/EngineResources/DefaultTexture",
                         "none-of-2-candidates", 1, 2, True,
                         [uv_head_note("texcoord-to-maskU", ncand),
                          uv_head_note("texcoord-to-maskV", ncand)],
                         *uv_head_fields([(False, "none-of-%d-candidates..then."
                                           "property-write-unavailable" % ncand,
                                           ncand, None)] * 2, ncand))
    checks += 1
    if [t for t in line.split() if t.count("=") != 1]:
        bad.append("the material line has a token that is not one key=value: %s"
                   % [t for t in line.split() if t.count("=") != 1])
    checks += 1
    if "materialStatus=PARTIAL" not in line or "materialScriptReturn=2" not in line:
        bad.append("the line does not carry the status and the return it was "
                   "built from: %s" % line)
    checks += 1
    if "materialDefaultsBound=1/2" not in line:
        bad.append("an engine default that did not resolve ships without its "
                   "denominator: %s" % line)
    checks += 1
    if "materialUvHeadVia=" not in line or \
            ("materialUvHeadTriedAtWorst=%d/%d" % (ncand, ncand)) not in line \
            or "materialUvHeadReadback=0/2..unreadable2" not in line:
        bad.append("the failing line does not carry what the UV head cost and "
                   "what read back: %s" % line)
    # AND THE PASSING SHAPE, which is what the acceptance of this item looks
    # like on the wire. A formatter only ever run over its failure case is
    # half a formatter.
    good_line = material_line(STATUS_MADE, 3, 3, 14, 14, True,
                              "/Engine/EngineResources/DefaultTexture",
                              "/Engine/EngineMaterials/DefaultNormal", 2, 2,
                              True, [],
                              *uv_head_fields([(True, win, 1, True)] * 2, ncand))
    checks += 1
    if [t for t in good_line.split() if t.count("=") != 1]:
        bad.append("the passing line has a token that is not one key=value: %s"
                   % [t for t in good_line.split() if t.count("=") != 1])
    checks += 1
    if "materialStatus=MADE" not in good_line or \
            "materialScriptReturn=0" not in good_line or \
            "materialConnections=14/14" not in good_line or \
            ("materialUvHeadVia=both.%s" % win) not in good_line or \
            "materialUvHeadReadback=2/2..unreadable0" not in good_line or \
            "materialNote=none" not in good_line:
        bad.append("the passing line is not what the acceptance asks for: %s"
                   % good_line)
    print("    %s" % line)
    print("    %s" % good_line)
    print("make_base_material --selftest: %d check(s), %d failure(s), "
          "params=%s scalars=%s header=%s"
          % (checks, len(bad), "/".join(TEXTURE_PARAMS), "/".join(SCALAR_PARAMS),
             os.path.relpath(header, root)))
    for b in bad:
        print("  FAIL %s" % b)
    return 0 if not bad else 2


def _reads_back(dst, src):
    """Read the graph back rather than trusting the editor's boolean.

    Returns True when the destination's input holds the source expression,
    False when it holds something else or nothing, and None when the editor
    will not answer at all (the input struct is not exposed to Python in this
    version). None is not no, and the verdict line carries the two apart.
    """
    try:
        got = dst.get_editor_property("input")
        if got is None:
            return False
        linked = got.get_editor_property("expression")
        return linked is not None and linked == src
    except Exception:
        return None


def _write_input_property(src, dst):
    """LAST RESORT, AND NAMED AS ONE ON THE VERDICT LINE. If no pin name is
    accepted, write the input struct directly and let the readback say whether
    it took. Still a script and still a build product: the D1 rule is that no
    human opens the editor, not that only one API may be used.

    Returns True only when the graph READS BACK connected, False when the
    write was refused or cannot be confirmed, and None when the property is
    not exposed at all. Confirmation is required because a struct written by
    value that the editor quietly discards would otherwise be counted as a
    connection and print MADE over an unwired material, which is the exact
    class of failure the 3 September rule exists to stop.
    """
    try:
        val = dst.get_editor_property("input")
    except Exception:
        return None
    if val is None:
        return None
    try:
        val.set_editor_property("expression", src)
        val.set_editor_property("output_index", 0)
        dst.set_editor_property("input", val)
    except Exception:
        return False
    return _reads_back(dst, src) is True


def _first_that_loads(unreal, paths):
    for p in paths:
        try:
            a = unreal.EditorAssetLibrary.load_asset(p)
            if a is not None:
                return a, p
        except Exception:
            continue
    return None, "none-of-%d-candidates" % len(paths)


def main():
    if "--selftest" in sys.argv:
        return selftest()

    import unreal  # only inside the editor; the selftest above never gets here

    w = Wiring()

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mel = unreal.MaterialEditingLibrary

    existed = unreal.EditorAssetLibrary.does_asset_exist(ASSET_PATH)
    if existed:
        # ALWAYS REGENERATED. The asset is a build product and this script is
        # its only writer; an asset kept from a previous run could not be
        # shown to match the script that claims to have made it.
        unreal.EditorAssetLibrary.delete_asset(ASSET_PATH)

    mat = tools.create_asset(ASSET, PACKAGE, unreal.Material,
                             unreal.MaterialFactoryNew())
    if mat is None:
        _write("materialStatus=CREATE-FAILED materialPath=%s "
               "materialNote=asset-tools-returned-nothing" % ASSET_PATH)
        unreal.log_error("LEDGER: could not create %s" % ASSET_PATH)
        return 2

    colour_default, colour_from = _first_that_loads(unreal, COLOUR_DEFAULTS)
    normal_default, normal_from = _first_that_loads(unreal, NORMAL_DEFAULTS)

    # ---- the UV chain: TexCoord masked, scaled per axis, appended ----------
    # Two scalars rather than one, because a 42 metre carriageway 2.7 metres
    # wide tiled uniformly is 21 repeats along AND across, and the across is
    # what a camera in the street is looking at.
    def expr(cls, x, y):
        return mel.create_material_expression(mat, cls, x, y)

    def connect(a, out, b, inp, what):
        try:
            ok = bool(mel.connect_material_expressions(a, out, b, inp))
        except Exception:
            return w.record(False, "%s-threw" % what)
        return w.record(ok, "%s-refused" % what)

    def connect_prop(a, out, prop, what):
        try:
            ok = bool(mel.connect_material_property(a, out, prop))
        except Exception:
            return w.record(False, "%s-threw" % what)
        return w.record(ok, "%s-refused" % what)

    # THE HEAD OF THE UV CHAIN, WHICH IS THE ONE PAIR OF NAMES THIS SCRIPT
    # COULD NOT ESTABLISH BEFORE THE RUN. See UV_PIN_CANDIDATES. One
    # connection is counted however many names it costs, so materialConnections
    # keeps the denominator 14 that runs 19 and 20 printed and the fraction
    # stays comparable across the three runs.
    uv_head = []

    def connect_uv_head(src, dst, what):
        ok, tried, out_name, in_name = connect_by_candidates(
            lambda o, i: mel.connect_material_expressions(src, o, dst, i),
            UV_PIN_CANDIDATES)
        if ok:
            via = pin_token(out_name, in_name)
        else:
            wrote = _write_input_property(src, dst)
            via = "none-of-%d-candidates..then.property-write-%s" % (
                len(UV_PIN_CANDIDATES),
                "took" if wrote is True else
                ("unavailable" if wrote is None else "refused"))
            ok = wrote is True
        uv_head.append((ok, via, tried, _reads_back(dst, src)))
        # The token runs 19 and 20 printed is kept as a PREFIX so a grep for
        # texcoord-to-maskU-refused still finds this line if it happens again.
        return w.record(ok, uv_head_note(what, len(UV_PIN_CANDIDATES)))

    tc = expr(unreal.MaterialExpressionTextureCoordinate, -1100, 0)
    mask_u = expr(unreal.MaterialExpressionComponentMask, -900, -80)
    mask_u.set_editor_property("r", True)
    mask_u.set_editor_property("g", False)
    mask_u.set_editor_property("b", False)
    mask_u.set_editor_property("a", False)
    mask_v = expr(unreal.MaterialExpressionComponentMask, -900, 80)
    mask_v.set_editor_property("r", False)
    mask_v.set_editor_property("g", True)
    mask_v.set_editor_property("b", False)
    mask_v.set_editor_property("a", False)
    su = expr(unreal.MaterialExpressionScalarParameter, -900, -160)
    su.set_editor_property("parameter_name", SCALAR_PARAMS[0])
    su.set_editor_property("default_value", 1.0)
    sv = expr(unreal.MaterialExpressionScalarParameter, -900, 160)
    sv.set_editor_property("parameter_name", SCALAR_PARAMS[1])
    sv.set_editor_property("default_value", 1.0)
    mul_u = expr(unreal.MaterialExpressionMultiply, -700, -80)
    mul_v = expr(unreal.MaterialExpressionMultiply, -700, 80)
    app = expr(unreal.MaterialExpressionAppendVector, -520, 0)

    connect_uv_head(tc, mask_u, "texcoord-to-maskU")
    connect_uv_head(tc, mask_v, "texcoord-to-maskV")
    connect(mask_u, "", mul_u, "A", "maskU-to-mulU")
    connect(su, "", mul_u, "B", "tilingU-to-mulU")
    connect(mask_v, "", mul_v, "A", "maskV-to-mulV")
    connect(sv, "", mul_v, "B", "tilingV-to-mulV")
    connect(mul_u, "", app, "A", "mulU-to-append")
    connect(mul_v, "", app, "B", "mulV-to-append")

    # ---- the three samplers -----------------------------------------------
    # Each is wired on its own. A material with a base colour and no normal
    # map is worth having; a script that gives up halfway is not.
    made = []

    def sampler(name, y, sampler_type, default_tex, prop, out_pin, label):
        s = expr(unreal.MaterialExpressionTextureSampleParameter2D, -300, y)
        s.set_editor_property("parameter_name", name)
        try:
            if default_tex is not None:
                s.set_editor_property("texture", default_tex)
            s.set_editor_property("sampler_type", sampler_type)
        except Exception:
            w.notes.append("%s-default-or-samplertype-refused" % label)
        connect(app, "", s, "UVs", "%s-uvs" % label)
        if connect_prop(s, out_pin, prop, "%s-out" % label):
            made.append(name)
        return s

    st = unreal.MaterialSamplerType
    mp = unreal.MaterialProperty
    sampler(TEXTURE_PARAMS[0], -300, st.SAMPLERTYPE_COLOR, colour_default,
            mp.MP_BASE_COLOR, "RGB", "basecolor")
    sampler(TEXTURE_PARAMS[1], 0, st.SAMPLERTYPE_NORMAL, normal_default,
            mp.MP_NORMAL, "RGB", "normal")
    sampler(TEXTURE_PARAMS[2], 300, st.SAMPLERTYPE_LINEAR_GRAYSCALE,
            colour_default, mp.MP_ROUGHNESS, "R", "roughness")

    try:
        mel.recompile_material(mat)
    except Exception:
        w.notes.append("recompile-threw")
    saved = False
    try:
        saved = bool(unreal.EditorAssetLibrary.save_asset(ASSET_PATH))
    except Exception:
        w.notes.append("save-threw")

    # THE ENGINE DEFAULTS SHIP A DENOMINATOR. `none-of-2-candidates` with no
    # total beside it cannot be told from a run that never looked.
    defaults_bound = (1 if colour_default is not None else 0) \
                   + (1 if normal_default is not None else 0)
    # A DEFAULT THAT DID NOT RESOLVE IS NOT WHAT DECIDES THE STATUS, and this
    # is the half of run 19 that was reported honestly: the asset saved at
    # 10474 bytes with no normal default and the packaged game then loaded it
    # (materialBase read loaded on the vignette verdict), so a missing engine
    # default did not stop the material being made. It is printed, counted
    # and left out of the verdict rather than being quietly promoted into it.
    uv_via, uv_tried, uv_readback = uv_head_fields(uv_head,
                                                   len(UV_PIN_CANDIDATES))
    status = material_status(saved, len(made), len(TEXTURE_PARAMS),
                             w.wired, w.asked)
    _write(material_line(status, len(made), len(TEXTURE_PARAMS),
                         w.wired, w.asked,
                         existed, colour_from, normal_from,
                         defaults_bound, 2, saved, w.notes,
                         uv_via, uv_tried, uv_readback))
    return material_return(status)


def _write(line):
    """The evidence channel is a file, not a log tail. Written beside the
    project so the workflow step can copy it into the build verdict."""
    try:
        import unreal
        root = unreal.Paths.project_dir()
    except Exception:
        root = "."
    path = os.path.join(root, "ue-material.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)
    try:
        import unreal
        unreal.log("LEDGER " + line)
    except Exception:
        pass


def _inside_unreal():
    try:
        import unreal  # noqa: F401
        return True
    except Exception:
        return False


if __name__ == "__main__":
    # SYS.EXIT IS FOR A REAL PROCESS ONLY. Inside the editor this file runs on
    # an embedded interpreter that is not exiting anything: raising SystemExit
    # there is a plausible way to turn a script that worked into a process
    # that reports failure, which is one half of the pair run 19 could not
    # explain. The verdict inside the editor travels in the file, as
    # materialScriptReturn, which is the channel this project trusts.
    _code = main()
    if _inside_unreal():
        print("make_base_material: returning %d without sys.exit "
              "(inside the editor; the verdict is materialScriptReturn in "
              "ue-material.txt)" % _code)
    else:
        sys.exit(_code)
