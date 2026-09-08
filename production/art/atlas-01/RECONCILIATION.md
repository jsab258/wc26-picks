# Revisions actually read

Continuation of reviewed delivery b81667e203415ff7b0f34622c3dcd1cc96139801. Owner source pin remains 7722b45cb3dcee2fbcee26675fae4fef641cbba7. No merge of the newer studio state into this art checkout.

On 2026-09-08, the remote art branch still pointed to the reviewed delivery and the isolated local checkout was clean on that commit. Its only worktree was this art checkout. The studio was read through GitHub at e5b33d1317e20d672e4f9e39c09e4db41d023e0f:

| Read | Finding |
|---|---|
| game-design/art-collaboration.md | Studio now records the same source pin; separate checkout and delivery/review convention; existing art consumer |
| production/specs/asset-interface.md | Metres, glTF +Y up and -Z forward; life-size meshes; placement uses bounds centre; one slot overwritten with a surface; no embedded images in current prop lane |
| .github/workflows/ledger-art-blender-preview.yml | Opt-in only. Checks out moving art branch, expects tools/art-recipes/NAME.py and `--out`, banks PNGs only |
| tools/art-deliveries.py | Creates one integration task per commission name. Already-filed task does not update itself for a later delivery |
| production/NOW.md | Read for current work; historical assertions were not treated as fresh execution evidence |
| ledger-v2/research/license-allowlist.md | CC0 sources permitted, licence tags required, fictional brands/vehicles, no new model/tool adoption here |
| Recursive studio tree | No production/art/atlas-01/REVIEW.md and no production/queue/art-atlas-01-integration.md at this revision. The review quoted by the owner is the repair brief; no fabricated studio review |
| Art Actions runs, branch-filtered API | 0 runs returned, total_count 0 at reconciliation. Check again before every push |
| Published pc-inbox / pc-results trees | No atlas recipe or atlas result identified. pc-results request at 3efd67eb962301745e635f2ef1fb22cdfe9be5b5 is `fetch-the-vignette-surfaces`, not an art preview |

Applicable local CLAUDE.md and pinned canon were reread. No AGENTS.md was found in the inspected studio tree. The owner's explicit commission scope governs the branch, art ownership, approval channel and no-scheduler/no-Telegram boundaries.

The new interface is real but narrow. It supports plain static props, not the proposed rich pub materials, hinged doors or complete interiors. See INTERFACE-NOTES.md. The workflow is a published route, not proof the recipe is runnable through it unchanged. No live daemon journal was accessed and no shared PC was reserved.

Continuation read: the same studio SHA's machine BOM (77 identical IDs), base-mesh THIRD-PARTY.md, eight actual GLBs, three existing generated PNGs, tools/imagegen/prompts.json and relevant validation/CLI paths in tools/imagegen/imagegen.py. The existing image lane is reused; its validator accepted the one-item pilot input locally without invoking generation. Read-only branch reconciliation near completion returned unchanged studio/pc-inbox/pc-results SHAs and art at the published repair/request commit 1e625318f6cfba8e7f939e9ec1a35210c3f53a60. No new REVIEW or equivalent pilot result had landed at those unchanged revisions. No merge, reset, rebase or force push was used.

Before this continuation push, GitHub Actions returned 0 in-progress and 0 queued runs; remote studio, pc-inbox and pc-results revisions were unchanged from the reads above. Art was still at 1e625318f6cfba8e7f939e9ec1a35210c3f53a60. The reviewed workflow triggers do not run on these art-only paths. No result-producing atlas job was found, and no branch was moved during banking.
