#!/usr/bin/env python3
"""Blender foreground: open every prop the pipeline made, laid out and labelled.

    blender --factory-startup --python view_props.py -- --props DIR [--lod LOD0]

READ-ONLY, AND CHECKED RATHER THAN PROMISED. This script imports meshes to
look at them. It never saves a .blend, never exports, never deletes and never
writes a byte into content/props. propview.py's selftest greps this file for
save_as_mainfile, export_scene, os.remove, rmtree and any open(..., "w") and
fails if it finds one, so the promise has an instrument behind it.

WHAT IT DOES, in order: empty the factory scene (the default cube would sit in
the middle of the batch), import each prop's LOD0, move it onto its own cell of
the grid propview.py computed, name its collection so the outliner reads as a
contents list, stand an upright label carrying the id and the measured size
over it, put a 1.8 m human-scale block at the left so proportions can be
judged, then frame the lot.

IT DOES NOT DECIDE ANYTHING. Which files are props, which LOD, what order and
what cell all come from propview.py, which is the layer with tests, and the
preflight that printed the count to the window before this window opened used
the same calls. The only numbers this file adds are Blender's own measured
bounds of what actually got imported, which it compares against the plan and
reports when they disagree.

UNRUN WHERE IT WAS WRITTEN. There is no Blender in this container. What is
checked from here is that it compiles and that the flags it reads are the
flags the .bat passes. The first double-click is its accepting case, and the
most likely first-run fault is the viewport framing at the end: if the view
opens badly, the Home key frames everything.
"""
import math
import os
import sys
import traceback

try:
    import bpy
    import mathutils
except ImportError:                       # not inside Blender: say so plainly
    bpy = None
    mathutils = None

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (HERE, os.path.dirname(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ONE IMPORTER, ONE LAYOUT. clean_lod.py already knows how to enable the glTF
# addon and import by extension, and it is the copy the grinder has actually
# run; propview.py owns discovery and the grid. Both are imported rather than
# reimplemented.
from clean_lod import ensure_addon, import_any                 # noqa: E402
import propview                                                # noqa: E402

#: The reference body. 1.8 m is a tall-ish adult, and the point is only that a
#: bench, a bollard and a lamp post can be judged against something whose size
#: a person already knows. Shoulder width 0.45 m, depth 0.25 m.
HUMAN_M = (0.45, 0.25, 1.8)


#: Label height in metres, clamped. The lower bound is legibility (below about
#: 7 cm a label is a smudge at the distance that frames a 10 m grid); the upper
#: bound stops a 3 m wide awning getting a label taller than a bollard.
LABEL_MIN_M, LABEL_MAX_M = 0.07, 0.16
#: Every second column has its label lifted by this much, so a long name over a
#: narrow prop (rounded_concrete_bollard is 24 characters over 0.19 m) cannot
#: land on its neighbour's label. Immediate neighbours are always in adjacent
#: columns, so they are never in the same height band.
LABEL_STAGGER_M = 0.34


def label_size(cell_w, text):
    """Text big enough to read at framing distance, small enough to stay in
    its own cell. Blender text size is roughly the cap height in metres and a
    line is about 0.5 * size * len(line) wide in the default font, so this
    solves for the longest line fitting the cell and then clamps."""
    longest = max((len(l) for l in text.splitlines()), default=1)
    by_width = cell_w / max(1.0, 0.5 * longest)
    return max(LABEL_MIN_M, min(LABEL_MAX_M, by_width))


def world_bounds_of(objs):
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for o in objs:
        for corner in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(corner)
            for k in range(3):
                lo[k] = min(lo[k], w[k])
                hi[k] = max(hi[k], w[k])
    if lo[0] == float("inf"):
        return None, None
    return lo, hi


def make_label(name, body, x, y, z, size):
    """A label standing UPRIGHT and facing the opening view, not lying on the
    floor. Floor text is legible from directly above and nowhere else, and the
    view that shows a prop's silhouette is a low one. Rotating 90 degrees about
    X stands the text in the XZ plane facing -Y, which is where the camera is."""
    bpy.ops.object.text_add(location=(x, y, z))
    t = bpy.context.object
    t.name = name
    t.data.body = body
    t.data.align_x = "CENTER"
    t.data.align_y = "BOTTOM"
    t.data.size = size
    t.data.extrude = 0.0
    t.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    return t


def make_human(x, y):
    """A plain block, not a mesh anybody could mistake for a prop. It is named
    so the outliner says what it is."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, HUMAN_M[2] / 2.0))
    h = bpy.context.object
    h.name = "SCALE_REFERENCE_person_1m80"
    h.scale = (HUMAN_M[0], HUMAN_M[1], HUMAN_M[2])
    try:
        # Wireframe so it cannot be mistaken for a 38th prop.
        h.display_type = "WIRE"
    except Exception:                                            # noqa: BLE001
        pass
    return h


def frame_the_view(centre, radius, notes):
    """Point every 3D viewport at the batch from the front, slightly above.

    THE OPERATOR IS THE FALLBACK, NOT THE PRIMARY. bpy.ops.view3d.view_all
    needs a context this script may not have at startup, and when its poll
    fails it raises rather than doing nothing. Setting the region's own view
    location, distance and rotation needs no poll at all, so that is done
    first and the operator is only a refinement."""
    done = 0
    for window in getattr(bpy.context.window_manager, "windows", []):
        for area in window.screen.areas:
            if area.type != "VIEW_3D":
                continue
            region3d = getattr(area.spaces.active, "region_3d", None)
            if region3d is None:
                continue
            try:
                region3d.view_perspective = "PERSP"
                region3d.view_location = mathutils.Vector(centre)
                region3d.view_distance = max(2.0, radius * 2.4)
                # Looking along +Y from the front, tilted 25 degrees down: the
                # front row is nearest and the silhouettes stay readable, which
                # a plain top view loses.
                region3d.view_rotation = mathutils.Euler(
                    (math.radians(65.0), 0.0, 0.0), "XYZ").to_quaternion()
                sp = area.spaces.active
                sp.shading.type = "SOLID"
                for attr, val in (("show_cavity", True), ("studio_light", "Default")):
                    try:
                        setattr(sp.shading, attr, val)
                    except Exception:                            # noqa: BLE001
                        pass
                done += 1
            except Exception as e:                               # noqa: BLE001
                notes.append("could not set a viewport: %s: %s"
                             % (type(e).__name__, e))
            try:
                region = next(r for r in area.regions if r.type == "WINDOW")
                with bpy.context.temp_override(window=window, area=area,
                                               region=region):
                    bpy.ops.view3d.view_all()
            except Exception as e:                               # noqa: BLE001
                notes.append("view_all did not run (%s); the view is placed by "
                             "hand instead, and the Home key reframes it"
                             % type(e).__name__)
    return done


def no_save_prompt(notes):
    """Nothing here writes, so quitting must not ask. --factory-startup means
    the preference is at its default, which does prompt."""
    try:
        prefs = bpy.context.preferences
        prefs.view.use_save_prompt = False
        # And do not let this run leave a changed preference behind either.
        prefs.use_preferences_save = False
    except Exception as e:                                       # noqa: BLE001
        notes.append("could not turn off the save prompt (%s); if it asks on "
                     "exit, the answer is Don't Save, and nothing was changed"
                     % type(e).__name__)


def build(args):
    """Everything that touches Blender. Returns how many props are ON SCREEN,
    which is the only number the caller is entitled to report."""
    notes = []
    props_dir = args["props"] or os.path.join(
        os.path.dirname(os.path.dirname(HERE)), "content", "props")
    cols = int(args["max-cols"]) if args["max-cols"] and args["max-cols"] != "1" else None
    r = propview.plan_for(props_dir, lod=args["lod"], max_cols=cols)
    plan = r["plan"]
    if not r["props"]:
        # The .bat stops before opening a window in this case; reaching here
        # means somebody ran this directly, so say the same thing rather than
        # sitting in an empty scene with no explanation.
        for line in propview.report(props_dir, r["props"], plan, r["manifest"],
                                    r["disc_notes"], r["meas_notes"],
                                    r["measured"], r["unread"], r["glb_files"]):
            print(line)
        return 0

    # THE PROMPT IS TURNED OFF BEFORE THE SCENE IS EMPTIED as well as after:
    # emptying is a File-New, which is the other place Blender can ask to save,
    # and read_factory_settings may reset what was set before it.
    no_save_prompt([])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ensure_addon("io_scene_gltf2")
    no_save_prompt(notes)
    scene_coll = bpy.context.scene.collection

    placed = failed = oversize = 0
    for pl in plan["placements"]:
        before = set(bpy.context.scene.objects)
        try:
            import_any(pl["path"])
        except Exception as e:                                   # noqa: BLE001
            failed += 1
            notes.append("%s did not import (%s: %s)"
                         % (pl["file"], type(e).__name__, e))
            continue
        fresh = [o for o in bpy.context.scene.objects if o not in before]
        meshes = [o for o in fresh if o.type == "MESH"]
        if not meshes:
            failed += 1
            notes.append("%s imported without a single mesh object" % pl["file"])
            for o in fresh:
                bpy.data.objects.remove(o, do_unlink=True)
            continue

        # MOVE IT BY ITS OWN MEASURED BOUNDS, not by its pivot: the pipeline
        # writes a base-centre pivot, but a prop that arrived some other way
        # must still land in the middle of its cell and on the floor.
        lo, hi = world_bounds_of(meshes)
        if lo:
            dx = pl["x"] - (lo[0] + hi[0]) / 2.0
            dy = pl["y"] - (lo[1] + hi[1]) / 2.0
            dz = -lo[2]
            for o in fresh:
                if o.parent is None:
                    o.location = (o.location[0] + dx, o.location[1] + dy,
                                  o.location[2] + dz)
            real_w, real_d = hi[0] - lo[0], hi[1] - lo[1]
            if real_w > pl["cell_w"] + 1e-3 or real_d > pl["cell_d"] + 1e-3:
                oversize += 1
                notes.append("%s measures %.2f x %.2f m in Blender but was "
                             "planned a %.2f x %.2f m cell, so it may reach "
                             "into its neighbour"
                             % (pl["id"], real_w, real_d, pl["cell_w"], pl["cell_d"]))

        # THE OUTLINER IS HALF THE LABELLING. One collection per prop, named
        # with the same index the printed list uses.
        name = "%02d %s" % (pl["index"], pl["id"])
        coll = bpy.data.collections.new(name)
        scene_coll.children.link(coll)
        for o in fresh:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            coll.objects.link(o)
        for i, o in enumerate(fresh):
            o.name = "%02d_%s%s" % (pl["index"], pl["id"],
                                    "" if i == 0 else "_%d" % (i + 1))

        body = "%02d %s\n%.2f x %.2f x %.2f m" % (
            pl["index"], pl["id"], pl["w"], pl["d"], pl["h"] or 0.0)
        top = (hi[2] - lo[2]) if lo else (pl["h"] or 0.0)
        t = make_label("label_%02d_%s" % (pl["index"], pl["id"]), body,
                       pl["x"], pl["y"] - pl["cell_d"] / 2.0 - 0.02,
                       top + 0.10 + (LABEL_STAGGER_M if pl["col"] % 2 else 0.0),
                       label_size(pl["cell_w"] + plan["gap"], body))
        for c in list(t.users_collection):
            c.objects.unlink(t)
        coll.objects.link(t)
        placed += 1

    width, depth = plan["extent"]
    try:
        human = make_human(-width / 2.0 - plan["gap"] - HUMAN_M[0],
                           -depth / 2.0 + HUMAN_M[1])
        make_label("label_scale_reference", "1.80 m person\nfor scale",
                   human.location[0], human.location[1] - HUMAN_M[1] - 0.1,
                   HUMAN_M[2] + 0.10, 0.14)
    except Exception as e:                                       # noqa: BLE001
        notes.append("no scale reference (%s: %s)" % (type(e).__name__, e))

    # AN EMPTY BLENDER LOOKS EXACTLY LIKE A WORKING BLENDER SHOWING NOTHING,
    # and the second reads as "the props are broken". So when nothing arrived,
    # the reason goes IN THE 3D VIEW at a size that cannot be missed, not only
    # in a console nobody scrolls back through.
    if placed == 0:
        try:
            make_label("NOTHING_LOADED",
                       "NOTHING LOADED\n%d prop file(s) were found and none "
                       "could be opened.\nClose this and send back the black "
                       "window behind it." % len(plan["placements"]),
                       0.0, 0.0, 0.6, 0.35)
        except Exception as e:                                   # noqa: BLE001
            notes.append("could not even draw the empty-scene banner (%s: %s)"
                         % (type(e).__name__, e))
        width = depth = 6.0
    elif failed:
        try:
            make_label("SOME_FAILED",
                       "%d of %d did not open. The gaps in the grid are them."
                       % (failed, len(plan["placements"])),
                       0.0, -depth / 2.0 - 1.2, 0.4, 0.25)
        except Exception:                                        # noqa: BLE001
            pass

    radius = max(width, depth) / 2.0 + 1.0
    viewports = frame_the_view((0.0, 0.0, 0.6), radius, notes)

    print("")
    print("  ---- what is on your screen ---------------------------------")
    print("  %d prop(s) placed, %d failed to import, %d of %d in the plan"
          % (placed, failed, placed + failed, len(plan["placements"])))
    print("  %d prop(s) measured bigger than their planned cell" % oversize)
    print("  laid out %d across and %d deep, %.1f x %.1f m, %.2f m apart"
          % (plan["cols"], plan["rows"], width, depth, plan["gap"]))
    print("  %d viewport(s) framed. If the view looks wrong, press Home over "
          "it." % viewports)
    print("  Nothing was saved and no file was changed. Close the window when "
          "you are done.")
    print("")
    print("  The order, left to right, front row first:")
    for pl in plan["placements"]:
        print("    %02d %-28s %5.2f x %5.2f x %5.2f m"
              % (pl["index"], pl["id"], pl["w"], pl["d"], pl["h"] or 0.0))
    for n in notes + r["disc_notes"] + r["meas_notes"]:
        print("  note: %s" % n)
    print("  -------------------------------------------------------------")
    return placed


def write_marker(path, placed):
    """The one line the .bat reads AFTER Blender closes, so "it opened and
    showed 37 props" and "it opened and showed nothing" are different words in
    the window rather than the same silence.

    WRITTEN IN A FINALLY, like clean_lod's result file and for the same
    reason: the interesting case is the one where this script raised, and an
    exit code cannot carry it because Blender returns 0 anyway."""
    if not path:
        return
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(("PLACED %d\n" % placed) if placed else "NOTHING 0\n")
    except OSError as e:
        print("view_props: could not write the marker file: %s" % e)


def main():
    argv = propview.script_argv()
    try:
        args = propview.parse_args(argv)
    except ValueError as e:
        print("view_props: %s" % e)
        return 2
    if bpy is None:
        print("view_props: this script must run inside Blender "
              "(blender --factory-startup --python view_props.py -- --props DIR)")
        return 2
    placed = 0
    try:
        placed = build(args)
    except Exception:                                            # noqa: BLE001
        # A raised script leaves Blender open with a half-built scene and
        # nothing said, because the traceback goes to a console nobody is
        # looking at by then. Print it where the .bat window is, and let the
        # marker below tell the .bat that nothing arrived.
        print("")
        print("  ---- the viewer failed --------------------------------------")
        traceback.print_exc()
        print("  Send back the lines above. Nothing was written or changed.")
        print("  -------------------------------------------------------------")
    finally:
        write_marker(args["status"], placed)
    return 0 if placed else 4


if __name__ == "__main__":
    main()
