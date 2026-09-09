#!/usr/bin/env python3
"""WHICH OF THE THREE IS MISSING FROM A COMMITTED FRAME: THE SUN, ITS SHADOWS,
OR THE OCCLUSION. Queue 197, the measurement half.

WHY THIS EXISTS. The rung-1 frame production/d1-probe/ue-vign_hook_day.png has
no dark in it (p05 0.32 against the reference panel's 0.12) and nothing in it
sits on the ground. By eye that is one observation with three causes, and rule
4 says a picture is strong evidence that something is wrong and weak evidence
of what. These three candidates look identical in a thumbnail:
  (a) no directional sun reaching the street, so everything is flat ambient,
  (b) a sun that shades faces but casts no shadow, so no object is seated,
  (c) a sun and shadows but no ambient occlusion, so recesses stay open.
They differ in the pixels, and this tool is what reads the difference off a
frame that is ALREADY COMMITTED. No dispatch, no render, no engine.

HOW IT SEPARATES THEM. The street's geometry, the sun's elevation and azimuth
and the camera are all in committed files, so the frame can be re-traced here:
  M1 FACE ORIENTATION, which needs no shadow map. A sun makes a face's
     brightness follow max(0,n.s): the street's two facades have opposite
     normals, so with ANY sun the -z facades read brighter than the +z ones,
     and with no sun they read alike. Taken PER SURFACE NAME so that two
     different albedos are never compared, and only over pixels this tool
     predicts are NOT in shadow, so a shadow cannot be read as shading.
  M2 GROUND SHADOW, which needs a shadow map. Every up-facing ground pixel is
     traced toward the sun through the same geometry the engine built. If the
     engine drew shadows, the predicted-shadowed pixels are darker than the
     predicted-lit ones IN THE SAME DEPTH BIN; if it did not, the two are the
     same brightness and the frame has no cast shadow in it.
  M3 CONTACT, which needs occlusion of the ambient. Over predicted-LIT ground
     pixels only, luma binned by horizontal distance to the nearest thing that
     rises above the ground there. Any occlusion path (SSAO, DFAO, a GI
     method) darkens the near bins; no occlusion path leaves the series flat.
THE LOGIC IS STATED BEFORE THE NUMBERS ARE READ, which is the point: M1 flat
means (a) and M2 says nothing, because a shadow of a light that is not there
is not a shadow. M1 asymmetric in the PREDICTED ORDER confirms the sun vector
off the pixels, and only then does a flat M2 mean shadows, and a flat M3 mean
occlusion.

WHAT IT IS NOT. It is a raytracer against boxes and cylinders, not a renderer:
it predicts where a shadow WOULD fall, never what the frame should look like.
Every approximation is counted on the output rather than argued about here:
mesh props are traced as the spec box they replaced, decal quads are traced as
visible but never as casters, cylinders are traced as cylinders, and the
skyline check prints its agreement separately per shape class so a wrong pivot
on 146 cylinders cannot hide inside one number.

THE INSTRUMENT IS CHECKED AGAINST THE ENGINE'S OWN READBACKS, because a
tracer that disagrees with the frame's projection would invent a shadow mask
and measure it confidently (rule 3):
  - the three control quads' pixel centres, which the engine MEASURED and
    printed in ue-vignette-verdict.txt, are reprojected here and compared;
  - the whole-frame mean luma is recomputed and compared to the engine's own
    shotMeanLuma for the same file;
  - the predicted skyline is compared per column to the frame's own, which is
    the check that the camera, the units and the frame conversion all agree.

Run:  python3 tools/frame-shadow-probe.py [--selftest] [--stride N]
"""

import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PIECES = os.path.join(ROOT, "production/specs/vignette-pieces.json")
FRAME = os.path.join(ROOT, "production/d1-probe/ue-vign_hook_day.png")
VERDICT = os.path.join(ROOT, "production/d1-probe/ue-vignette-verdict.txt")

SHOT_ID = "vign_hook_day"
CAM_ID = "cam_hook"

# THE SAME LUMA WEIGHTS THE VERDICT AND THE UNITY SIM USE, character for
# character, so that this tool's numbers and the engine's are the same kind of
# number. The cross-check below is what proves they are.
LUMA_W = np.array([0.299, 0.587, 0.114], dtype=np.float64)

# SKY IS A LUMA, NOT A REGION, and the number is MEASURED not chosen: the
# engine's own band.skyCentre reads mean 0.9323 with spread 0.0078 over 23040
# px of pure sky in this frame, so 0.90 is below every sky pixel that band saw
# and is used only to find the skyline for the instrument check. It is not a
# bound on anything the conclusion rests on.
SKY_LUMA = 0.90

EPS = 0.05  # cm, the offset a shadow ray starts at off its own surface


# ---------------------------------------------------------------------------
# the engine's own conventions, copied rather than re-derived
# ---------------------------------------------------------------------------

def rotation_rows(pitch_deg, yaw_deg, roll_deg):
    """UE's FRotationMatrix, rows = the rotated X (forward), Y (right), Z (up).

    Transcribed from the engine's matrix, not re-derived: the forward row is
    (cosP cosY, cosP sinY, sinP), which is the row the control-quad check
    below exercises against a pixel the engine itself measured.
    """
    p = math.radians(pitch_deg)
    y = math.radians(yaw_deg)
    r = math.radians(roll_deg)
    sp, cp = math.sin(p), math.cos(p)
    sy, cy = math.sin(y), math.cos(y)
    sr, cr = math.sin(r), math.cos(r)
    return np.array([
        [cp * cy, cp * sy, sp],
        [sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp],
        [-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp],
    ], dtype=np.float64)


def local_to_world(pitch_deg, yaw_deg, roll_deg):
    """Columns are the local axes in world space: world = R @ local."""
    return rotation_rows(pitch_deg, yaw_deg, roll_deg).T


def horizontal_fov_deg(fov_v_deg, w, h):
    """The probe's HorizontalFovDeg: the file's fov is vertical, UE's is
    horizontal. Same arithmetic, and the verdict prints both so the pair can
    be compared (fovV=39.0/fovH=64.4 on the hook line)."""
    t = math.tan(math.radians(fov_v_deg) * 0.5) * (float(w) / float(h))
    return math.degrees(2.0 * math.atan(t))


# ---------------------------------------------------------------------------
# primitives, built exactly as SpawnPiece builds actors
# ---------------------------------------------------------------------------

class Prim:
    __slots__ = ("kind", "c", "R", "h", "name", "surface", "shape", "edge",
                 "caster", "aabb_lo", "aabb_hi")

    def __init__(self, kind, c, R, h, piece, caster):
        self.kind = kind            # 'box' or 'cyl'
        self.c = c                  # centre, world cm
        self.R = R                  # local -> world
        self.h = h                  # half extents, local cm (cyl: x=y=radius, z=half height)
        self.name = piece["name"]
        self.surface = piece["surface"]
        self.shape = piece["shape"]
        self.edge = piece["edge"]
        self.caster = caster
        corners = np.array([[sx, sy, sz] for sx in (-h[0], h[0])
                            for sy in (-h[1], h[1])
                            for sz in (-h[2], h[2])], dtype=np.float64)
        w = corners @ R.T + c
        self.aabb_lo = w.min(axis=0)
        self.aabb_hi = w.max(axis=0)

    def corners_world(self):
        h = self.h
        corners = np.array([[sx, sy, sz] for sx in (-h[0], h[0])
                            for sy in (-h[1], h[1])
                            for sz in (-h[2], h[2])], dtype=np.float64)
        return corners @ self.R.T + self.c


def build_prims(pieces, decal_lift_cm=1.0):
    """One primitive per piece, with the engine's frame conversion and
    rotation mapping: (X,Y,Z)=(x,z,y)*100, Pitch=roll, Yaw=yaw, Roll=-pitch.

    A mesh piece is traced as the spec box it would have fallen back to. The
    run that took this frame placed 22 of 23 as real meshes whose world AABB
    was measured 0.00 mm off the file's centre and at worst 44.02 mm off the
    box's size, so the box is the right stand-in and the error is bounded by
    that reading rather than by this comment.
    """
    prims = []
    counts = {"box": 0, "cyl": 0, "mesh_as_box": 0, "decal": 0, "skipped": 0}
    for p in pieces:
        c = np.array([p["x_m"] * 100.0, p["z_m"] * 100.0, p["y_m"] * 100.0])
        pitch_ue = p["roll_deg"]
        yaw_ue = p["yaw_deg"]
        roll_ue = -p["pitch_deg"]
        shape = p["shape"]
        if shape in ("box", "mesh"):
            h = np.array([p["sx_m"], p["sz_m"], p["sy_m"]]) * 50.0
            R = local_to_world(pitch_ue, yaw_ue, roll_ue)
            prims.append(Prim("box", c, R, h, p, True))
            counts["mesh_as_box" if shape == "mesh" else "box"] += 1
        elif shape == "cyl":
            # Radius from sx/sz, height from sy, axis local +Z, which is the
            # file's local +y: the piece file states that axis for both
            # engines and VignetteShot.cpp relies on the same fact.
            h = np.array([p["sx_m"] * 50.0, p["sz_m"] * 50.0, p["sy_m"] * 50.0])
            R = local_to_world(pitch_ue, yaw_ue, roll_ue)
            prims.append(Prim("cyl", c, R, h, p, True))
            counts["cyl"] += 1
        elif shape == "decal":
            # The emitter turns the plane onto the file's facing with
            # pitch-90 in the FILE's frame, then lifts it 1 cm along its own
            # local +Z. Visible, never a caster: its shadow is displaced
            # ~1.4 cm, which is sub-pixel at every distance this camera sees.
            roll_q = -(p["pitch_deg"] - 90.0)
            R = local_to_world(pitch_ue, yaw_ue, roll_q)
            c2 = c + R[:, 2] * decal_lift_cm
            h = np.array([p["sx_m"] * 50.0, p["sy_m"] * 50.0, 0.5])
            prims.append(Prim("box", c2, R, h, p, False))
            counts["decal"] += 1
        else:
            counts["skipped"] += 1
    return prims, counts


# ---------------------------------------------------------------------------
# intersection, vectorised per primitive over a set of rays
# ---------------------------------------------------------------------------

def hit_box(o, d, prim, want_normal=True):
    """o,d: (N,3). Returns t (N,) with inf for a miss, and normals (N,3)."""
    R = prim.R
    ol = (o - prim.c) @ R
    dl = d @ R
    with np.errstate(divide="ignore", invalid="ignore"):
        inv = 1.0 / dl
        t1 = (-prim.h - ol) * inv
        t2 = (prim.h - ol) * inv
    tlo = np.minimum(t1, t2)
    thi = np.maximum(t1, t2)
    tlo = np.nan_to_num(tlo, nan=-np.inf)
    thi = np.nan_to_num(thi, nan=np.inf)
    t0 = tlo.max(axis=1)
    t1e = thi.min(axis=1)
    hit = (t0 < t1e) & (t1e > EPS)
    t = np.where(t0 > EPS, t0, t1e)
    t = np.where(hit, t, np.inf)
    if not want_normal:
        return t, None
    ax = np.argmax(tlo, axis=1)
    rows = np.arange(o.shape[0] if o.shape[0] > 1 else d.shape[0])
    nloc = np.zeros((rows.size, 3))
    dsel = dl[rows if dl.shape[0] > 1 else 0, ax] if dl.shape[0] > 1 else dl[0, ax]
    nloc[rows, ax] = -np.sign(dsel)
    n = nloc @ R.T
    return t, n


def hit_cyl(o, d, prim, want_normal=True):
    """Finite cylinder, axis local Z, radius h[0] (h[1] asserted equal)."""
    R = prim.R
    r = prim.h[0]
    hz = prim.h[2]
    ol = (o - prim.c) @ R
    dl = d @ R
    if dl.shape[0] == 1 and ol.shape[0] > 1:
        dl = np.repeat(dl, ol.shape[0], axis=0)
    if ol.shape[0] == 1 and dl.shape[0] > 1:
        ol = np.repeat(ol, dl.shape[0], axis=0)
    n = ol.shape[0]
    best = np.full(n, np.inf)
    bestn = np.zeros((n, 3))
    a = dl[:, 0] ** 2 + dl[:, 1] ** 2
    b = 2.0 * (ol[:, 0] * dl[:, 0] + ol[:, 1] * dl[:, 1])
    cq = ol[:, 0] ** 2 + ol[:, 1] ** 2 - r * r
    disc = b * b - 4.0 * a * cq
    ok = (a > 1e-18) & (disc >= 0.0)
    if ok.any():
        sq = np.zeros(n)
        sq[ok] = np.sqrt(disc[ok])
        for sign in (-1.0, 1.0):
            with np.errstate(divide="ignore", invalid="ignore"):
                t = (-b + sign * sq) / (2.0 * a)
            z = ol[:, 2] + t * dl[:, 2]
            good = ok & np.isfinite(t) & (t > EPS) & (np.abs(z) <= hz) & (t < best)
            if good.any():
                best = np.where(good, t, best)
                px = ol[:, 0] + t * dl[:, 0]
                py = ol[:, 1] + t * dl[:, 1]
                nl = np.stack([px / r, py / r, np.zeros(n)], axis=1)
                bestn = np.where(good[:, None], nl, bestn)
    for sign in (-1.0, 1.0):
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (sign * hz - ol[:, 2]) / dl[:, 2]
            px = ol[:, 0] + t * dl[:, 0]
            py = ol[:, 1] + t * dl[:, 1]
            good = (np.isfinite(t) & (t > EPS) & (px * px + py * py <= r * r)
                    & (t < best))
        if good.any():
            best = np.where(good, t, best)
            nl = np.zeros((n, 3))
            nl[:, 2] = sign
            bestn = np.where(good[:, None], nl, bestn)
    if not want_normal:
        return best, None
    return best, bestn @ R.T


def hit_prim(o, d, prim, want_normal=True):
    if prim.kind == "box":
        return hit_box(o, d, prim, want_normal)
    return hit_cyl(o, d, prim, want_normal)


# ---------------------------------------------------------------------------
# the camera
# ---------------------------------------------------------------------------

class Cam:
    def __init__(self, pos_cm, pitch_deg, yaw_deg, fov_v_deg, w, h):
        self.pos = np.asarray(pos_cm, dtype=np.float64)
        rows = rotation_rows(pitch_deg, yaw_deg, 0.0)
        self.fwd, self.right, self.up = rows[0], rows[1], rows[2]
        self.w, self.h = w, h
        self.tan_h = math.tan(math.radians(horizontal_fov_deg(fov_v_deg, w, h)) * 0.5)
        self.tan_v = math.tan(math.radians(fov_v_deg) * 0.5)

    def project(self, pts):
        v = np.asarray(pts, dtype=np.float64) - self.pos
        zf = v @ self.fwd
        x = v @ self.right
        y = v @ self.up
        with np.errstate(divide="ignore", invalid="ignore"):
            px = 0.5 * self.w * (1.0 + (x / zf) / self.tan_h)
            py = 0.5 * self.h * (1.0 - (y / zf) / self.tan_v)
        return px, py, zf

    def rays(self):
        xs = (np.arange(self.w) + 0.5) / self.w * 2.0 - 1.0
        ys = 1.0 - (np.arange(self.h) + 0.5) / self.h * 2.0
        gx, gy = np.meshgrid(xs, ys)
        d = (self.fwd[None, None, :]
             + self.right[None, None, :] * (gx * self.tan_h)[:, :, None]
             + self.up[None, None, :] * (gy * self.tan_v)[:, :, None])
        d /= np.linalg.norm(d, axis=2, keepdims=True)
        return d


# ---------------------------------------------------------------------------
# verdict parsing: the engine's own readbacks are the inputs, never my guesses
# ---------------------------------------------------------------------------

def verdict_keys(path):
    out = {}
    lines = []
    first = "unknown"
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh):
            if i == 0:
                # LINE 1 NAMES THE COMMIT THE FRAME WAS MEASURED ON, which is
                # the fact that ties every number here to one run.
                toks = line.split()
                first = toks[3] if len(toks) > 3 else "unknown"
            if line.startswith("#") or not line.strip():
                continue
            lines.append(line.rstrip("\n"))
            for tok in line.split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    out.setdefault(k, v)
    return out, lines, first


def shot_keys(lines, shot_id):
    for line in lines:
        if line.startswith("shot " + shot_id + " "):
            d = {}
            for tok in line.split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    d[k] = v
            return d
    return None


def quad_lines(lines):
    out = []
    for line in lines:
        if line.startswith("controlQuad="):
            d = {}
            for tok in line.split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    d[k] = v
            out.append(d)
    return out


# ---------------------------------------------------------------------------
# stats helpers
# ---------------------------------------------------------------------------

def stat4(a):
    """mean/p05/p50/p95 of a luma sample, or the words for an empty one."""
    if a.size == 0:
        return "nothing-measured"
    return "%.4f/%.4f/%.4f/%.4f" % (float(a.mean()),
                                    float(np.percentile(a, 5)),
                                    float(np.percentile(a, 50)),
                                    float(np.percentile(a, 95)))


def say(out, line):
    out.append(line)


# ---------------------------------------------------------------------------
# the run
# ---------------------------------------------------------------------------

def trace_frame(cam, prims, out, stride_shadow=2, stride_contact=4,
                sun_toward=None):
    """Primary trace, then the shadow and contact passes. Returns a dict."""
    dirs = cam.rays()
    H, W = cam.h, cam.w
    zbuf = np.full((H, W), np.inf)
    pidx = np.full((H, W), -1, dtype=np.int32)
    nrm = np.zeros((H, W, 3))
    full = 0
    for i, pr in enumerate(prims):
        cw = pr.corners_world()
        px, py, zf = cam.project(cw)
        if np.any(zf <= 1.0) or not np.all(np.isfinite(px)):
            x0, x1, y0, y1 = 0, W, 0, H
            full += 1
        else:
            x0 = max(0, int(math.floor(px.min())) - 1)
            x1 = min(W, int(math.ceil(px.max())) + 1)
            y0 = max(0, int(math.floor(py.min())) - 1)
            y1 = min(H, int(math.ceil(py.max())) + 1)
            if x0 >= x1 or y0 >= y1:
                continue
        sub = dirs[y0:y1, x0:x1].reshape(-1, 3)
        o = cam.pos[None, :]
        t, n = hit_prim(o, sub, pr, want_normal=True)
        t = t.reshape(y1 - y0, x1 - x0)
        n = n.reshape(y1 - y0, x1 - x0, 3)
        zs = zbuf[y0:y1, x0:x1]
        better = t < zs
        if better.any():
            zbuf[y0:y1, x0:x1] = np.where(better, t, zs)
            ps = pidx[y0:y1, x0:x1]
            pidx[y0:y1, x0:x1] = np.where(better, i, ps)
            ns = nrm[y0:y1, x0:x1]
            nrm[y0:y1, x0:x1] = np.where(better[:, :, None], n, ns)
    hits = pidx >= 0
    say(out, "traceFullFramePrims=%d/%d traceHitPx=%d/%d traceHitPct=%.2f"
        " traceStat=nearest-hit-per-pixel/one-frame"
        % (full, len(prims), int(hits.sum()), H * W,
           100.0 * float(hits.sum()) / (H * W)))
    return {"dirs": dirs, "zbuf": zbuf, "pidx": pidx, "nrm": nrm, "hits": hits}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--stride-shadow", type=int, default=2)
    ap.add_argument("--stride-contact", type=int, default=4)
    ap.add_argument("--frame", default=FRAME)
    ap.add_argument("--verdict", default=VERDICT)
    ap.add_argument("--pieces", default=PIECES)
    ap.add_argument("--shot", default=SHOT_ID)
    ap.add_argument("--camera", default=CAM_ID)
    # FAIL-CLOSED BY DEFAULT. A verdict written before queue 208 carries only
    # a one-per-run shotCam line describing the LAST camera the run placed.
    # Reading a frame whose camera that line does not describe needs this
    # flag, which names itself on the output, and the control-quad
    # reprojection is then the only evidence the camera is right.
    ap.add_argument("--camera-from-json", action="store_true")
    ap.add_argument("--dump-mask", default=None)
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    out = []
    run(out, args.stride_shadow, args.stride_contact, pieces_path=args.pieces,
        frame_path=args.frame, verdict_path=args.verdict, shot_id=args.shot,
        cam_id=args.camera, cam_from_json=args.camera_from_json,
        dump_mask=args.dump_mask)
    print("\n".join(out))
    return 0


def run(out, stride_shadow, stride_contact, pieces_path=PIECES,
        frame_path=FRAME, verdict_path=VERDICT, shot_id=SHOT_ID,
        cam_id=CAM_ID, cam_from_json=False, dump_mask=None):
    spec = json.load(open(pieces_path, "r", encoding="utf-8"))
    keys, lines, commit = verdict_keys(verdict_path)
    shot = shot_keys(lines, shot_id)
    if shot is None:
        say(out, "probeStatus=NO-SHOT probeNote=no-line-for-" + shot_id
            + " probe=nothing-measured")
        return out
    say(out, "# frame-shadow-probe: off committed files only, no engine, no dispatch.")
    say(out, "# Every count ships its denominator; every number names what it is a"
             " statistic OF.")
    say(out, "probeInputs=%s+%s+%s"
        % (os.path.relpath(frame_path, ROOT), os.path.relpath(pieces_path, ROOT),
           os.path.relpath(verdict_path, ROOT)))
    say(out, "probeFrameCommit=%s probeShot=%s probeCamera=%s"
        % (commit, shot_id, cam_id))

    # ---- the camera, taken from the engine's own readback ----------------
    # FAIL CLOSED. Whichever line the pose came off, it is only the hook
    # camera's if its eye height and yaw match the hook shot's. If they do
    # not, this tool must refuse rather than trace a camera that took a
    # different picture.
    cam_json = None
    for c in spec["cameras"]:
        if c["id"] == cam_id:
            cam_json = c
    if cam_json is None:
        say(out, "probeStatus=NO-CAMERA probeNote=no-" + cam_id
            + "-in-the-pieces-file probe=nothing-measured")
        return out
    # QUEUE 208: THE POSE IS A PER-SHOT KEY NOW, AND THIS IS THE ONLY THING
    # THAT CHANGED IN THIS TOOL. It reads the SHOT's own camera keys when the
    # verdict carries them and falls back to the one-per-run line when it does
    # not, so a verdict written before 2026-09-09 reads exactly as it did.
    # Which source answered is printed, because a bind off the run line is
    # last-wins and a bind off the shot line is not, and nothing else here
    # could tell them apart. Nothing below this block moved: the rule, the
    # tolerances and every measurement are untouched.
    cam_src = "shot-line" if "shotCamReadXYZcm" in shot else "run-line-one-per-run"
    src = shot if cam_src == "shot-line" else keys
    try:
        read_xyz = [float(v) for v in src["shotCamReadXYZcm"].split("/")]
        read_py = [float(v) for v in src["shotCamReadPitchYaw"].split("/")]
    except (KeyError, ValueError):
        # A POSE THE VERDICT COULD NOT MEASURE IS NOT A POSE AT THE ORIGIN.
        say(out, "camBind=REFUSED camBindFrom=%s camReadXYZcm=nothing-measured"
                 " camReadPitchYaw=nothing-measured"
                 " camBindRule=this-shots-own-camera-keys-must-match-this-shots-eye-and-this-cameras-angles"
            % cam_src)
        say(out, "probeStatus=REFUSED probe=nothing-measured")
        return out
    eye_shot = float(shot["eye"].split("/")[0])
    bind_ok = (abs(read_xyz[2] / 100.0 - eye_shot) <= 0.01
               and abs(read_py[1] - cam_json["yaw_deg"]) <= 0.05
               and abs(read_py[0] + cam_json["pitch_deg"]) <= 0.05
               and abs(read_xyz[0] / 100.0 - cam_json["x_m"]) <= 0.01
               and abs(read_xyz[1] / 100.0 - cam_json["z_m"]) <= 0.01)
    say(out, "camBind=%s camBindFrom=%s camReadXYZcm=%.1f/%.1f/%.1f camReadPitchYaw=%.1f/%.1f"
             " camShotEyeM=%.3f camJsonXZYawPitch=%.1f/%.1f/%.1f/%.1f"
             " camBindRule=this-shots-own-camera-keys-must-match-this-shots-eye-and-this-cameras-angles"
        % ("MATCHES-" + cam_id if bind_ok
           else ("FROM-JSON-AND-SHOT-EYE/the-quad-reprojection-below-is-the-evidence"
                 if cam_from_json else "REFUSED"),
           cam_src,
           read_xyz[0], read_xyz[1], read_xyz[2], read_py[0], read_py[1],
           eye_shot, cam_json["x_m"], cam_json["z_m"], cam_json["yaw_deg"],
           cam_json["pitch_deg"]))
    if not bind_ok and not cam_from_json:
        say(out, "probeStatus=REFUSED probe=nothing-measured")
        return out
    W = int(shot["shotW"])
    H = int(shot["shotH"])
    fov_v = float(shot["fovV"].split("/")[0].replace("fovV", ""))
    if bind_ok:
        cam = Cam(read_xyz, read_py[0], read_py[1], fov_v, W, H)
    else:
        cam = Cam([cam_json["x_m"] * 100.0, cam_json["z_m"] * 100.0,
                   eye_shot * 100.0],
                  -cam_json["pitch_deg"], cam_json["yaw_deg"], fov_v, W, H)
    say(out, "camFovVH=%.1f/%.1f camFovFromVerdict=%s"
        % (fov_v, horizontal_fov_deg(fov_v, W, H), shot["fovV"]))

    # ---- the frame ------------------------------------------------------
    img = Image.open(frame_path).convert("RGB")
    if img.size != (W, H):
        say(out, "probeStatus=SIZE-MISMATCH probeImg=%dx%d probeVerdict=%dx%d"
            " probe=nothing-measured" % (img.size[0], img.size[1], W, H))
        return out
    rgb = np.asarray(img, dtype=np.float64) / 255.0
    luma = rgb @ LUMA_W
    mine = float(luma.mean())
    theirs = float(shot["shotMeanLuma"])
    say(out, "lumaCrossCheck=mine/%.4f=engine/%.4f delta=%.4f"
             " lumaCrossStat=mean-over-every-pixel/one-frame/same-weights-as-the-verdict"
        % (mine, theirs, abs(mine - theirs)))
    say(out, "frameLuma=mean/p05/p50/p95=%s frameLumaOf=%d"
        % (stat4(luma.reshape(-1)), luma.size))

    # ---- the geometry ---------------------------------------------------
    prims, pcounts = build_prims(spec["pieces"])
    say(out, "prims=%d/%d asBox=%d asCyl=%d meshAsBox=%d decalVisibleNotCaster=%d"
             " skipped=%d casters=%d"
        % (len(prims), len(spec["pieces"]), pcounts["box"], pcounts["cyl"],
           pcounts["mesh_as_box"], pcounts["decal"], pcounts["skipped"],
           sum(1 for p in prims if p.caster)))

    tr = trace_frame(cam, prims, out)
    pidx, nrm, zbuf, hits = tr["pidx"], tr["nrm"], tr["zbuf"], tr["hits"]

    # ---- INSTRUMENT CHECK 1: the control quads the engine measured -------
    qs = quad_lines(lines)
    agree = 0
    worst = 0.0
    worst_on = "nothing-measured"
    cam_a = None
    for c in spec["cameras"]:
        if c["id"] == "cam_A":
            cam_a = c
    # The quads were placed for cam_A and the engine printed their pixel
    # centres from THAT camera, so the check is done with cam_A's transform
    # rebuilt the same way PlaceCamera builds it. eye comes off the camA shot
    # line, which is the engine's own reading of the footway it stands on.
    shot_a = shot_keys(lines, "vign_camA_day")
    qcam = None
    if cam_a is not None and shot_a is not None:
        eye_a = float(shot_a["eye"].split("/")[0])
        qcam = Cam([cam_a["x_m"] * 100.0, cam_a["z_m"] * 100.0, eye_a * 100.0],
                   -cam_a["pitch_deg"], cam_a["yaw_deg"],
                   float(shot_a["fovV"].split("/")[0]), W, H)
    for q in qs:
        if qcam is None or "quadReadXYZcm" not in q or "quadCentrePx" not in q:
            continue
        xyz = [float(v) for v in q["quadReadXYZcm"].split("/")]
        cx, cy = [float(v) for v in q["quadCentrePx"].split("/")]
        px, py, _ = qcam.project(np.array([xyz]))
        d = math.hypot(float(px[0]) - cx, float(py[0]) - cy)
        if d <= 2.0:
            agree += 1
        if d > worst:
            worst = d
            worst_on = q["controlQuad"]
    say(out, "quadReproject=%d/%d within2px quadWorstPx=%.2f/on=%s"
             " quadStat=engine-printed-pixel-centre-versus-this-tools-projection/at-worst"
        % (agree, len(qs), worst, worst_on))

    # ---- INSTRUMENT CHECK 2: the skyline, per column --------------------
    sky = luma >= SKY_LUMA
    first_geo = np.where(hits.any(axis=0), hits.argmax(axis=0), -1)
    notsky = ~sky
    first_dark = np.where(notsky.any(axis=0), notsky.argmax(axis=0), -1)
    both = (first_geo >= 0) & (first_dark >= 0)
    dd = np.abs(first_geo[both] - first_dark[both]).astype(np.float64)
    say(out, "skylineCols=%d/%d skylineAbsDeltaPx=median/p95=%s"
             " skylineStat=topmost-predicted-geometry-row-minus-topmost-non-sky-row/per-column"
        % (int(both.sum()), W,
           "nothing-measured" if dd.size == 0
           else "%.1f/%.1f" % (float(np.median(dd)), float(np.percentile(dd, 95)))))
    # AND SPLIT BY SHAPE CLASS, because a wrong pivot on 146 cylinders would
    # hide inside one median. Columns are attributed to the shape of the
    # primitive at their topmost predicted row.
    shapes = np.array([p.shape for p in prims] + ["none"])
    top_idx = np.where(both, pidx[np.clip(first_geo, 0, H - 1),
                                  np.arange(W)], -1)
    for cls in ("box", "cyl", "mesh", "decal"):
        sel = both & np.array([(0 <= i < len(prims)) and prims[i].shape == cls
                               for i in top_idx])
        d2 = np.abs(first_geo[sel] - first_dark[sel]).astype(np.float64)
        say(out, "skylineShape.%s=cols/%d absDeltaMedianPx=%s"
            % (cls, int(sel.sum()),
               "nothing-measured" if d2.size == 0 else "%.1f" % float(np.median(d2))))

    # ---- the sun, from the file, and ONE shadow pass over every sampled
    # ---- hit pixel -------------------------------------------------------
    #
    # ONE MASK, USED BY ALL THREE MEASUREMENTS. The first version of this tool
    # traced shadow rays for the ground only and then computed M1 over every
    # hit pixel, shadowed or not, which is not the measurement its own design
    # says it is: on the pre-sky frame of 7a3fa3e, where M2 shows a cast
    # shadow plainly, that M1 read a median of -0.0534 with four of six
    # surfaces the wrong way round, because a sunward face sitting in another
    # building's shadow was being counted as a sunward face. The fix is to
    # trace the whole sample once and let every measurement take its own
    # subset of the SAME mask.
    sun = spec["sun"]
    elev = float(sun["elevation_deg"])
    azi = float(sun["azimuth_deg"])
    sun_pitch = -elev                       # SunPitchDeg
    sun_yaw = (azi + 180.0) % 360.0         # SunYawDeg
    fwd = rotation_rows(sun_pitch, sun_yaw, 0.0)[0]
    toward = -fwd
    say(out, "sunFromFile=elev/%.1f+azi/%.1f sunUEPitchYaw=%.1f/%.1f"
             " sunTravelUE=%.3f/%.3f/%.3f sunTowardUE=%.3f/%.3f/%.3f"
             " sunRule=SunPitchDeg=-elev/SunYawDeg=azi+180/VignetteSpec.h"
        % (elev, azi, sun_pitch, sun_yaw, fwd[0], fwd[1], fwd[2],
           toward[0], toward[1], toward[2]))

    hy, hx = np.nonzero(hits)
    keep = (hy % stride_shadow == 0) & (hx % stride_shadow == 0)
    hy, hx = hy[keep], hx[keep]
    snrm = nrm[hy, hx]
    pts = (cam.pos[None, :] + tr["dirs"][hy, hx] * zbuf[hy, hx][:, None]
           + snrm * 0.5)
    occl = shadow_mask(pts, toward, prims)
    sluma = luma[hy, hx]
    sdepth = zbuf[hy, hx] / 100.0
    surf_all = np.array([p.surface for p in prims] + ["none"])
    ssurf = surf_all[np.where(pidx[hy, hx] >= 0, pidx[hy, hx], len(prims))]
    snds = snrm @ toward
    say(out, "sample=%d/%d stride=%d samplePredictedShadowed=%d/%d=%.2fpct"
             " sampleStat=one-shadow-trace-per-sampled-hit-pixel/shared-by-M1-M2-M3"
        % (hy.size, int(hits.sum()), stride_shadow, int(occl.sum()), hy.size,
           100.0 * float(occl.sum()) / max(1, hy.size)))

    # ---- M2: the ground, predicted-shadowed against predicted-lit --------
    up = snrm[:, 2]
    ground = up > 0.95
    ground_all = int(((nrm[:, :, 2] > 0.95) & hits).sum())
    say(out, "groundPx=%d/%d groundPct=%.2f groundSampled=%d/%d"
             " groundRule=hit-with-world-normal-z-over-0.95"
        % (ground_all, H * W, 100.0 * float(ground_all) / (H * W),
           int(ground.sum()), ground_all))
    gl = sluma[ground]
    go = occl[ground]
    gd = sdepth[ground]
    gs = ssurf[ground]
    say(out, "M2.groundLit=n/%d mean/p05/p50/p95=%s"
        % (int((~go).sum()), stat4(gl[~go])))
    say(out, "M2.groundShadowed=n/%d mean/p05/p50/p95=%s"
        % (int(go.sum()), stat4(gl[go])))
    if go.any() and (~go).any():
        say(out, "M2.litMinusShadowedMean=%+.4f"
                 " M2.rule=a-rendered-shadow-makes-this-positive-and-large/"
                 "no-shadow-makes-it-zero-or-negative"
            % (float(gl[~go].mean() - gl[go].mean())))
    # PER SURFACE, WHICH IS THE HALF THAT STOPS AN ALBEDO DIFFERENCE READING
    # AS A SHADOW: a kerb top reads 0.96 in this frame and asphalt 0.78, so a
    # predicted-shadow set with a different surface mix from the lit set would
    # differ by albedo alone.
    for sname in sorted(set(gs.tolist())):
        m = gs == sname
        aa = gl[m & ~go]
        bb = gl[m & go]
        if aa.size < 50 or bb.size < 50:
            say(out, "M2.surf.%s=lit/n%d shadowed/n%d diff=nothing-measured"
                     "/under-50-in-one-half" % (sname, aa.size, bb.size))
            continue
        say(out, "M2.surf.%s=lit/n%d/mean%.4f shadowed/n%d/mean%.4f diff=%+.4f"
            % (sname, aa.size, float(aa.mean()), bb.size, float(bb.mean()),
               float(aa.mean() - bb.mean())))
    # AND IN DEPTH BINS, because the shadowed region sits further down the
    # street than the lit one and the fog is a function of depth. The same
    # comparison inside one bin is the half that controls for it. ASPHALT
    # ONLY, so the bins are one material.
    asph = gs == "asphalt"
    edges = [0, 5, 10, 20, 40, 1e9]
    for k in range(len(edges) - 1):
        m = asph & (gd >= edges[k]) & (gd < edges[k + 1])
        aa = gl[m & ~go]
        bb = gl[m & go]
        say(out, "M2.asphaltDepth%sto%sm=lit/n%d/mean%s shadowed/n%d/mean%s diff=%s"
            % (edges[k], ("inf" if edges[k + 1] > 1e8 else edges[k + 1]),
               aa.size, "nothing-measured" if aa.size == 0 else "%.4f" % aa.mean(),
               bb.size, "nothing-measured" if bb.size == 0 else "%.4f" % bb.mean(),
               "nothing-measured" if (aa.size == 0 or bb.size == 0)
               else "%+.4f" % (aa.mean() - bb.mean())))

    # ---- M2b: THE SHADOW EDGE, WHICH IS THE SHARPEST FORM OF M2 ---------
    #
    # WHY A SECOND FORM. M2 compares two POPULATIONS of ground pixels, and the
    # shadowed one sits further down the street than the lit one, so fog and
    # albedo both get a vote however carefully the surfaces are split. The
    # edge does not have that problem: pixels a few pixels either side of a
    # predicted shadow boundary are the same material at the same distance in
    # the same fog, so a step across the boundary is a shadow and nothing
    # else. ASPHALT ONLY and inside one depth band, and both halves of the
    # profile ship their counts.
    #
    # THE BANDS ARE IN SAMPLE-LATTICE STEPS, which is stride_shadow image
    # pixels; at this camera and 5 to 15 m a pixel is about 5 to 15 mm on the
    # ground, so the whole profile below spans under 20 cm of road and a
    # directional light's shadow edge is sharp on that scale.
    lat_h = (H + stride_shadow - 1) // stride_shadow
    lat_w = (W + stride_shadow - 1) // stride_shadow
    ly = hy[ground] // stride_shadow
    lx = hx[ground] // stride_shadow
    in_m = np.zeros((lat_h, lat_w), dtype=bool)
    out_m = np.zeros((lat_h, lat_w), dtype=bool)
    subj = (gs == "asphalt") & (gd >= 4.0) & (gd <= 15.0)
    in_m[ly[go & subj], lx[go & subj]] = True
    out_m[ly[(~go) & subj], lx[(~go) & subj]] = True
    lum_l = np.zeros((lat_h, lat_w))
    lum_l[ly, lx] = gl

    def grow(m):
        g2 = m.copy()
        g2[1:, :] |= m[:-1, :]
        g2[:-1, :] |= m[1:, :]
        g2[:, 1:] |= m[:, :-1]
        g2[:, :-1] |= m[:, 1:]
        return g2

    say(out, "M2b.rule=mean-luma-of-asphalt-between-4m-and-15m-by-signed-lattice-distance"
             "-to-the-predicted-shadow-boundary/negative-is-inside-the-predicted-shadow/"
             "one-lattice-step-is-%d-image-px" % stride_shadow)
    # HOW WIDE THE PROFILE GOES, AND WHY IT IS NOT NARROWER. A first version
    # stopped at 6 lattice steps and read a step of +0.0088 on the 7a3fa3e
    # frame whose shadow M2 sees plainly, because 6 steps is about 10 cm of
    # road at this distance and the PREDICTED edge is not that accurate: the
    # caster can be a mesh traced as its 44 mm-tolerance box and the road has
    # a 1-in-40 crossfall. 24 steps is about 0.4 m at 7 m, which is wide
    # enough to straddle an edge placed that well and still narrow enough that
    # both sides are the same material at the same distance. The near bands
    # are PRINTED rather than dropped so a reader can see the smear.
    KNEAR, KFAR = 9, 24
    prof = []
    reach = out_m.copy()
    rem = in_m.copy()
    for k in range(1, KFAR + 1):
        reach = grow(reach)
        band = rem & reach
        rem = rem & ~band
        prof.append((-k, lum_l[band], int(band.sum())))
    reach = in_m.copy()
    rem = out_m.copy()
    for k in range(1, KFAR + 1):
        reach = grow(reach)
        band = rem & reach
        rem = rem & ~band
        prof.append((k, lum_l[band], int(band.sum())))
    prof.sort(key=lambda r: r[0])
    for (k, vals, n) in prof:
        if abs(k) % 3 and abs(k) > 3:
            continue
        say(out, "M2b.band%+d=n/%d mean=%s"
            % (k, n, "nothing-measured" if n == 0 else "%.4f" % float(vals.mean())))
    ins = [v for (k, v, n) in prof if -KFAR <= k <= -KNEAR and n]
    outs = [v for (k, v, n) in prof if KNEAR <= k <= KFAR and n]
    inside = np.concatenate(ins) if ins else np.array([])
    outside = np.concatenate(outs) if outs else np.array([])
    if inside.size >= 50 and outside.size >= 50:
        say(out, "M2b.stepOutsideMinusInside=%+.4f outsideN=%d insideN=%d"
                 " M2b.stat=mean-over-lattice-bands-%d-to-%d-either-side-of-the-predicted"
                 "-boundary/asphalt-only/4m-to-15m/one-frame"
            % (float(outside.mean() - inside.mean()), outside.size, inside.size,
               KNEAR, KFAR))
    else:
        say(out, "M2b.stepOutsideMinusInside=nothing-measured outsideN=%d insideN=%d"
            % (outside.size, inside.size))

    # THE MASK AS A PICTURE, because rule 4 says open the artifact: the
    # numbers above are only about the right pixels if the predicted shadow
    # lands where the geometry says it should.
    if dump_mask:
        vis = (np.dstack([luma, luma, luma]) * 255.0).astype(np.uint8)
        mk = np.zeros((H, W), dtype=bool)
        gy, gx = hy[ground], hx[ground]
        mk[gy[go], gx[go]] = True
        vis[mk, 0] = 255
        vis[mk, 1] = np.minimum(vis[mk, 1], 60)
        vis[mk, 2] = np.minimum(vis[mk, 2], 60)
        lit = np.zeros((H, W), dtype=bool)
        lit[gy[~go], gx[~go]] = True
        vis[lit, 2] = 255
        vis[lit, 0] = np.minimum(vis[lit, 0], 60)
        Image.fromarray(vis).save(dump_mask)
        say(out, "maskDump=%s maskRed=ground-predicted-shadowed"
                 " maskBlue=ground-predicted-lit" % os.path.basename(dump_mask))

    # ---- M1: face orientation, per surface, PREDICTED-LIT PIXELS ONLY ----
    axis_names = {(0, 1.0): "+x", (0, -1.0): "-x", (1, 1.0): "+z",
                  (1, -1.0): "-z", (2, 1.0): "+y", (2, -1.0): "-y"}
    ax = np.argmax(np.abs(snrm), axis=1)
    sgn = np.sign(snrm[np.arange(snrm.shape[0]), ax])
    say(out, "M1.rule=mean-luma-per-surface-and-face-class-over-PREDICTED-LIT-sampled-pixels/"
             "nDotS-is-the-suns-cosine-for-that-class/"
             "a-sun-orders-the-classes-by-nDotS-and-no-sun-leaves-them-level")
    m1_rows = []
    for sname in sorted(set(ssurf.tolist())):
        rows = []
        vert = []
        for (aa2, g), nm in sorted(axis_names.items(), key=lambda kv: kv[1]):
            m = (~occl) & (ssurf == sname) & (ax == aa2) & (sgn == g)
            if m.sum() < 60:
                continue
            nds = float(snds[m].mean())
            rows.append("%s:n%d/nDotS%.3f/mean%.4f"
                        % (nm, int(m.sum()), nds, float(sluma[m].mean())))
            # VERTICAL CLASSES ONLY for the tally: an up-facing face sees the
            # whole sky and a down-facing one sees almost none, so comparing
            # those measures sky visibility, not the sun. The four vertical
            # classes see about the same half-sky as each other, which is
            # what makes their spread attributable to the sun.
            if aa2 != 2:
                vert.append((nm, max(0.0, nds), float(sluma[m].mean()),
                             int(m.sum())))
        if rows:
            say(out, "M1.%s=%s" % (sname, "+".join(rows)))
        if len(vert) >= 2:
            vert.sort(key=lambda r: r[1])
            lo, hi = vert[0], vert[-1]
            m1_rows.append((sname, lo, hi, hi[1] - lo[1], hi[2] - lo[2]))

    # THE TALLY, AND IT IS THE WHOLE OF M1. Per surface: the vertical face
    # class with the largest sun cosine against the one with the smallest.
    # A sun raises the first above the second in proportion to the cosine
    # gap; no sun leaves them level. lumaPerCos is the luma gap divided by the
    # cosine gap. wrongSign counts the surfaces where the MORE sunlit class is
    # the DARKER one, which direct sun cannot do and a remaining confound can.
    if m1_rows:
        wrong = 0
        gaps = []
        for (sname, lo, hi, dn, dl) in m1_rows:
            if dn < 0.15:
                continue
            gaps.append(dl / dn)
            if dl < 0.0:
                wrong += 1
            say(out, "M1.vert.%s=lit%s/nDotS%.3f/mean%.4f/n%d"
                     " vs dark%s/nDotS%.3f/mean%.4f/n%d dCos=%.3f dLuma=%+.4f"
                     " lumaPerCos=%+.4f"
                % (sname, hi[0], hi[1], hi[2], hi[3], lo[0], lo[1], lo[2],
                   lo[3], dn, dl, dl / dn))
        if gaps:
            g = np.array(gaps)
            say(out, "M1.verticalTally=surfaces/%d lumaPerCosMedian=%+.4f"
                     " lumaPerCosMax=%+.4f wrongSign=%d/%d"
                     " M1.tallyStat=median-and-max-over-surfaces-with-a-cosine-gap"
                     "-over-0.15/predicted-lit-pixels-only/one-frame"
                % (g.size, float(np.median(g)), float(g.max()), wrong, g.size))
        else:
            say(out, "M1.verticalTally=nothing-measured"
                     " M1.tallyNote=no-surface-has-two-vertical-classes-0.15-apart-in-cosine")
    else:
        say(out, "M1.verticalTally=nothing-measured M1.tallyNote=no-lit-vertical-class-over-60px")

    # ---- M3: contact, over predicted-LIT ground pixels only -------------
    gpts = pts[ground]
    keep3 = (~go) & (np.arange(gl.size) % max(1, stride_contact // stride_shadow) == 0)
    p3 = gpts[keep3]
    l3 = gl[keep3]
    if p3.shape[0] == 0:
        say(out, "M3=nothing-measured M3Note=no-predicted-lit-ground-sample")
    else:
        dist = nearest_riser_cm(p3, prims)
        say(out, "M3.rule=mean-luma-of-predicted-LIT-ground-pixels-binned-by-horizontal"
                 "-distance-to-the-nearest-piece-whose-top-is-over-10cm-above-that-point/"
                 "occlusion-darkens-the-near-bins")
        bins = [0, 10, 25, 50, 100, 200, 400, 1e9]
        for k in range(len(bins) - 1):
            m = (dist >= bins[k]) & (dist < bins[k + 1])
            say(out, "M3.d%sto%scm=n/%d mean/p05/p50/p95=%s"
                % (bins[k], ("inf" if bins[k + 1] > 1e8 else bins[k + 1]),
                   int(m.sum()), stat4(l3[m])))
        # M3b: THE SAME QUESTION WITH THE DEPTH HELD STILL, which is the half
        # M3 cannot answer. A pixel near a kerb face is also a pixel near the
        # camera, so M3's series is partly a fog series. Here the depth band
        # and the surface are both fixed and only the distance to the riser
        # varies, which is the axis occlusion actually varies on. A kerb
        # upstand is 0.13 m high and runs the length of the street, so if any
        # occlusion path is reaching the ambient, the first bin is darker than
        # the last one. If it is not, nothing is occluding the sky here.
        for dname, dlo, dhi in (("4to8m", 4.0, 8.0), ("8to15m", 8.0, 15.0)):
            for sname in ("asphalt", "sidewalk"):
                sel = ((gs[keep3] == sname) & (gd[keep3] >= dlo)
                       & (gd[keep3] < dhi))
                if sel.sum() < 200:
                    say(out, "M3b.%s.%s=n/%d nothing-measured/under-200"
                        % (sname, dname, int(sel.sum())))
                    continue
                dd2 = dist[sel]
                ll2 = l3[sel]
                parts = []
                for lo2, hi2 in ((0, 15), (15, 40), (40, 100), (100, 300)):
                    mm = (dd2 >= lo2) & (dd2 < hi2)
                    parts.append("%dto%dcm:n%d/%s"
                                 % (lo2, hi2, int(mm.sum()),
                                    "none" if mm.sum() < 20
                                    else "%.4f" % float(ll2[mm].mean())))
                say(out, "M3b.%s.%s=%s" % (sname, dname, "+".join(parts)))
        say(out, "M3.sampleOf=%d/%d M3.confound=distance-also-correlates-with"
                 "-camera-depth/the-lit-only-restriction-removes-the-cast-shadow-not-the-fog"
            % (l3.size, int(ground.sum())))
    return out


def spec_surfaces(spec):
    return [p["surface"] for p in spec["pieces"]]


def shadow_mask(pts, toward, prims):
    """Any-hit along one shared direction. The active set shrinks as rays are
    found occluded, which is what makes a full ground pass affordable."""
    n = pts.shape[0]
    occl = np.zeros(n, dtype=bool)
    idx = np.arange(n)
    d = toward[None, :]
    for pr in prims:
        if not pr.caster:
            continue
        if idx.size == 0:
            break
        t, _ = hit_prim(pts[idx], d, pr, want_normal=False)
        got = np.isfinite(t)
        if got.any():
            occl[idx[got]] = True
            idx = idx[~got]
    return occl


def nearest_riser_cm(pts, prims):
    """Horizontal distance from each point to the nearest primitive world AABB
    whose top is more than 10 cm above the point. A PROXY for occlusion, named
    as one: a conservative AABB over a rotated piece over-reaches, and a wall
    on one side is not a wall all round."""
    lo = np.array([p.aabb_lo for p in prims])
    hi = np.array([p.aabb_hi for p in prims])
    best = np.full(pts.shape[0], 1e9)
    for i in range(lo.shape[0]):
        over = hi[i, 2] - pts[:, 2] > 10.0
        if not over.any():
            continue
        dx = np.maximum(np.maximum(lo[i, 0] - pts[:, 0], pts[:, 0] - hi[i, 0]), 0.0)
        dy = np.maximum(np.maximum(lo[i, 1] - pts[:, 1], pts[:, 1] - hi[i, 1]), 0.0)
        d = np.hypot(dx, dy)
        best = np.where(over & (d < best), d, best)
    return best


# ---------------------------------------------------------------------------
# selftest: the accepting case FIRST, on the live committed frame
# ---------------------------------------------------------------------------

def selftest():
    fails = []
    checks = 0

    # ACCEPT 1: the live frame traces, and every instrument check inside it
    # passes. The bounds below were set AFTER reading the series off this
    # frame, and each one says what it is.
    out = []
    run(out, 4, 8)
    text = "\n".join(out)
    print(text)
    print("# ---- selftest ----")

    def need(cond, label):
        nonlocal checks
        checks += 1
        if not cond:
            fails.append(label)

    kv = {}
    for line in out:
        for tok in line.split():
            if "=" in tok and not line.startswith("#"):
                k, v = tok.split("=", 1)
                kv.setdefault(k, v)
    need(kv.get("camBind", "").startswith("MATCHES"), "camBind")
    need("probeStatus" not in kv, "probeStatus-should-be-absent-on-a-good-run")
    # mean luma against the engine's own: measured at 0.0003 on this frame,
    # so 0.002 is a ceiling above the reading and not a number chosen first.
    m = [l for l in out if l.startswith("lumaCrossCheck=")][0]
    delta = float(m.split("delta=")[1].split()[0])
    need(delta <= 0.002, "lumaCrossCheck-delta=%.4f" % delta)
    q = [l for l in out if l.startswith("quadReproject=")][0]
    need(q.split("=")[1].split()[0] == "3/3", "quadReproject=" + q)
    sk = [l for l in out if l.startswith("skylineAbsDeltaPx") or "skylineAbsDeltaPx=" in l][0]
    med = float(sk.split("skylineAbsDeltaPx=median/p95=")[1].split("/")[0])
    need(med <= 6.0, "skylineMedianPx=%.1f" % med)

    # ACCEPT 2: a box straight ahead is hit at its own face, and the normal
    # points back at the camera. The one case the whole tool rests on.
    piece = {"name": "t", "surface": "s", "shape": "box", "edge": "e",
             "x_m": 10.0, "y_m": 0.0, "z_m": 0.0, "sx_m": 2.0, "sy_m": 2.0,
             "sz_m": 2.0, "pitch_deg": 0.0, "yaw_deg": 0.0, "roll_deg": 0.0}
    prims, _ = build_prims([piece])
    t, n = hit_prim(np.array([[0.0, 0.0, 0.0]]), np.array([[1.0, 0.0, 0.0]]),
                    prims[0])
    need(abs(t[0] - 900.0) < 1e-6, "box-t=%.3f" % t[0])
    need(abs(n[0][0] + 1.0) < 1e-9, "box-normal=%s" % n[0])

    # ACCEPT 3: a cylinder of radius 0.5 m at 10 m is hit 9.5 m out and its
    # normal is radial.
    cyl = dict(piece, shape="cyl", sx_m=1.0, sz_m=1.0, sy_m=4.0)
    prims, _ = build_prims([cyl])
    t, n = hit_prim(np.array([[0.0, 0.0, 0.0]]), np.array([[1.0, 0.0, 0.0]]),
                    prims[0])
    need(abs(t[0] - 950.0) < 1e-6, "cyl-t=%.3f" % t[0])
    need(abs(n[0][0] + 1.0) < 1e-9, "cyl-normal=%s" % n[0])

    # ACCEPT 4: a wall between a point and the sun occludes it, AND the same
    # point with the wall moved behind it does not. Both outcomes watched.
    # 24 m long, not 8: the sun ray from the origin crosses this wall's plane
    # 4.3 m along the street, so an 8 m wall centred on the origin ends before
    # the crossing and the accepting case would miss for a reason that has
    # nothing to do with the tracer. Measured from the ray, not guessed.
    wall = dict(piece, x_m=0.0, z_m=-2.0, y_m=2.0, sx_m=24.0, sy_m=4.0, sz_m=0.2)
    prims, _ = build_prims([wall])
    toward = -rotation_rows(-36.0, 25.0, 0.0)[0]
    pt = np.array([[0.0, 0.0, 0.0]])          # UE cm, on the road at origin
    m1 = shadow_mask(pt, toward, prims)
    far = dict(wall, z_m=+40.0)
    prims2, _ = build_prims([far])
    m2 = shadow_mask(pt, toward, prims2)
    need(bool(m1[0]), "shadow-accepting-case-missed")
    need(not bool(m2[0]), "shadow-rejecting-case-fired")

    # REJECT: a verdict whose camera line belongs to another camera must be
    # refused rather than traced. Synthetic, so doing the work this tool
    # prompts can never break the tool.
    import tempfile
    with open(VERDICT, "r", encoding="utf-8", errors="replace") as fh:
        body = fh.read()
    body = body.replace("shotCamReadXYZcm=400.0/-210.0/159.8",
                        "shotCamReadXYZcm=400.0/-210.0/167.2")
    tmp = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
    tmp.write(body)
    tmp.close()
    out2 = []
    run(out2, 16, 16, verdict_path=tmp.name)
    os.unlink(tmp.name)
    joined = "\n".join(out2)
    need("camBind=REFUSED" in joined and "probeStatus=REFUSED" in joined,
         "wrong-camera-was-not-refused")

    print("selftestChecks=%d/%d selftestFailed=%d/%d %s"
          % (checks - len(fails), checks, len(fails), checks,
             "selftestFails=" + ";".join(fails) if fails else "selftestFails=none"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
