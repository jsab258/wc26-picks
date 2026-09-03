# The visual bar's reference frames

> **STATUS: SPEC.** Five GTA V (PS3-era) street frames, supplied by Jafar.
> Frames 1-3 on 21 Aug 2026 (decomposed in `visual-bar-spec.md` §2), frames
> 4-5 re-supplied with the set on 24 Aug. **These ARE the bar** — M17.10's
> done-test is our noon/dusk/night stills beside these, called met by Jafar.

They are committed byte-exact because on 21 Aug they were decomposed in
prose and the pixels were kept only in a chat context, which was compacted;
for three days the project's visual target existed as a description of
itself. A file in the repository is the one channel that survives
compaction, rollback and session death — that is rule 12, and this
directory is its application to the most important artifact the project
has.

| file | what carries the frame |
|---|---|
| `gta5_1_liquor_store_side_sun` | long soft shadows grounding everything; a four-layer wall (stucco, poster residue, mural, water stains); dense street furniture in one static shot |
| `gta5_2_dusk_vespucci` | almost nothing but light: low warm sun, silhouetted poles and WIRES, one specular streak on the car |
| `gta5_3_overcast_morning` | THE KILLER ARGUMENT: no interesting light, still fully real — five asphalt tones, tar seams, patched repairs; dirt+depth+density with no sun |
| `gta5_4_suburban_bmx_noon` | clear noon, suburban: cracked concrete slabs with grass seams, low fences, loose rocks, roofline variety, towers + palms in haze |
| `gta5_5_ps3_sidewalk` | PS3-labelled: shadow dapple on a sidewalk, leaning poles, a stained wall, foreclosure sign — texture density at PLAYER height |

Measured, not only looked at: `tools/ref-bench.py` (when it lands) runs the
SAME statistics on these and on our committed stills — one instrument on
both sides, or the comparison is two instruments arguing.

Private-repo reference copies for internal development comparison; not for
redistribution.
