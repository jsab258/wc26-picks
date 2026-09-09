line: instrument
spec: tools/lint-bootstrap-single.py derives the needs-the-bootstrap set from each job's
  runs-on. A runs-on it cannot resolve (a matrix expression, an expression referencing a
  variable) currently has no way to be exempted with a reason, so the first matrix workflow
  meets a red nobody can clear without loosening the lint. Give an unresolvable runs-on its
  own exemption channel with a written reason, distinct from the exemption for a workflow
  that resolves and genuinely does not need the bootstrap.
acceptance: the live tree prints 0 unresolvable of 21 jobs, a planted matrix workflow with
  no exemption goes red naming it, and the same workflow with a written reason passes and is
  counted separately from the ordinary exemptions.
max_sessions: 1
status: READY 2026-09-09, item A of
  game-design/decision-2026-09-09-ruling-the-sun-the-bootstrap-and-the-board.md section 6.
  NOT URGENT AND NOT SPECULATIVE: the lint already prints
  "0 job(s) with a runs-on this lint cannot resolve of 21", so the case is measured as empty
  today and the item exists so that the day it stops being empty is not the day somebody
  loosens a guard under pressure.
