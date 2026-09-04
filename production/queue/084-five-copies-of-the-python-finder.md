line: infrastructure (the PC launchers)
spec: game-design/decision-2026-09-04-ruling-067-telegram-bot-first-pass.md, section 5
acceptance: one shared tools/runner/find-python.cmd, all five launchers calling it, and a two-sided lint that fails when a .bat inlines its own finder and passes on the shared call; the accepting case is the five live launchers
max_sessions: 1
status: READY 2026-09-04. Low priority, real debt, no drift yet. engine-specialist, small.

## The count, and the correction to my own premise

Five .bat files now carry an identical six-line `:trypy` Python finder:
`START THE STUDIO MACHINE.bat`, `open-dashboard.bat`,
`tools/meshgen/1 MAKE THE PROPS.bat`, `tools/imagegen/1 MAKE THE PICTURES.bat`
and `START THE TELEGRAM BOT.bat`.

I filed this believing `lint-bootstrap-single.py` would go red on the fifth
copy. THE DIRECTOR CORRECTED THAT: that lint is about the workflow PATH
bootstrap and does not look at these files at all. So nothing is failing, and
nothing WILL fail; this is silent debt rather than a breakage, which is why it
is low priority and why it needs a lint of its own to stop being invisible.

The builder matching the convention rather than extracting mid-pass was the
right call under a hard cap. Six executable lines identical across five copies,
no drift between them yet, is the moment to extract: before the copies start
disagreeing, and while a diff can still prove they were the same.

## The lint is the point, not the extraction

An extraction with no guard becomes six copies the next time someone writes a
launcher. The lint fails on an inlined finder and passes on the shared call,
and its accepting fixture is the five real launchers after the change.
