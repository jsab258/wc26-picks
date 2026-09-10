line: instrument (the restart evidence)
spec: The restart job's evidence prints, beside botSourceSha256, that the value is the
  hash of the file AS WINDOWS CHECKED IT OUT, and names the transform a reader in the
  container must apply to reproduce it.
acceptance: a reader with only the evidence file and the repository can reproduce the
  value, proved by doing it in the selftest for both line-ending forms
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-09. Found by predicting the wrong hash in a commit message.
  MEASURED: the file's LF hash here is DE848FBA7B1E8348, its CRLF hash is
  C0EA5105AFDB5BEE, and his machine reported C0EA5105AFDB5BEE. Git translates line
  endings on checkout for Windows, so THE TWO PARTIES CAN NEVER AGREE ON THIS VALUE and
  both are hashing the right file.
  WHY IT MATTERS MORE THAN IT SOUNDS: this key is read at the one moment somebody is
  anxious about whether a remote restart took effect, and a mismatch reads as failure. A
  successful restart would be reported as a failed one, and the obvious next action,
  restarting again, would change nothing and confirm the wrong story.
  THE FIX IS A SENTENCE, NOT A CODE CHANGE: name the transform beside the key. Do not
  "fix" it by hashing normalised bytes on his side, because then the value would stop
  describing the file the process actually loaded, which is the thing it exists to
  describe.
