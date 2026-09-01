line: infrastructure (D1 probe)
spec: production/d1-probe/plan.md, week 1 item 1
acceptance: UE5 launches on the build PC; version and disk noted here
max_sessions: 1
status: BLOCKED 2026-08-31, external dependency, not retryable by an agent

JAFAR ACTION: install Unreal Engine 5 on the build PC.

BLOCKED. The Epic Games Launcher will not offer any engine version to this
account. Symptom recorded in full so a later attempt or Epic support starts
from evidence rather than from memory:

- Launcher installed, signed in as JacquesCoppér, Unreal Engine tab reachable.
- ENGINE VERSIONS section is EMPTY. The "+" control beside it is GREYED OUT,
  which is the diagnostic: not a dead button, a launcher that believes zero
  engine versions are available to the account.
- "Install Engine" (yellow, top right) does nothing on click. Its dropdown
  arrow also does nothing.
- Download indicator reads 0.0 B. Fab Library vault reads empty.
- Tried and did not help: the "+" control; the dropdown arrow; relaunching
  the launcher as administrator; deleting %LOCALAPPDATA%\EpicGamesLauncher\
  Saved\webcache_4430 (the only webcache folder present) and relaunching;
  accepting the Unreal Engine licence at unrealengine.com/download;
  updating/reinstalling the launcher; searching the Store tab, where Unreal
  Engine does not appear as a product either.

READING: an entitlement or account-provisioning state, not a UI fault and
not a disk or permissions fault. Every symptom is consistent with the
account having no UE entitlement at all rather than with a broken install.
Next step if resumed is Epic account support with this list, which is why
the list is here.

CONSEQUENCE, and it is smaller than it looks: D1's Unity-side measurements
are real work regardless and now run first (tasks 002 to 004). The probe's
comparison half waits; its decision rule already says ties go to Unity, so
an unmeasurable UE side does NOT hand Unity the decision by default. If UE
cannot be measured at all, D1 closes as UNRESOLVED with the reason, never as
"Unity wins because the other engine would not install".
