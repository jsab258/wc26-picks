line: signage/brand
spec: production/specs/brand-bible-v1.md
acceptance: canon-gate clean; tools/brand-verify.py ships with its selftest and passes; the four minted names read from canon.md and unchanged; every entry has a register and a physical presence
max_sessions: 2

Author content/brands/brand-bible-v1.json to the spec, and ship
tools/brand-verify.py with it.

The verifier is not optional and not a follow-up. A brand bible with no
check is a document that decays the first time somebody adds a ninth entry,
and this project's whole record is of documents that decayed silently.
