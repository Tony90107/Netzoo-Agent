# Jev read of a request-level form condition row (2026-10-28) — declared before code

User decision (2026-10-28): fix the remaining problems in order, starting with J01's wrong reason. Declare gates,
measure offline, then ask. Branch `jev-conditions` (from `jev-permissive`, whose code equals main df806e15).

## Problem (jev-forms RESULTS.md, "missed readings")

h2hyb J01: "I want to understand gene regulation during zebrafish fin regeneration: five time points, four
replicates each, bulk RNA-seq." The reading typed the request-level condition `time_model=dynamic` with the quote "five
time points". That quote is inside no ask, so `requirement_split.condition_requirements` gives it a result row of its
own, credited to nothing. Its line says "No registered workflow models how the system changes from one time point to
the next", a reason the user never gave. Both Jev hooks (`forms_doubts`, the overlap ROUND-2 rule) run only on ask
rows, so this row is never read.

## Change (only with the flags on: forms read for time_model/spatial, overlap read for group_membership)

In `capability_check`, the rows `condition_requirements` returns go through a new `jev_forms.condition_doubts`. For
each row, the form it limits (`limiting_forms` with no credits: time_model dynamic, spatial uses_neighbors; and
group_membership several_groups through the overlap reader) is read by Jev on the same frozen question, with the row's
quote as the part. A doubted form is added to the row's `doubted_forms`, so `_form_reasons` does not say it, exactly as
on an ask row credited to nothing (forms round 1 / overlap ROUND-2). The row's status, credits and waits do not change,
so no call changes.

## Population (`scan.py`)

Every recorded reading under docs/research-log whose form condition is quoted outside every ask: **1 reading**
(h2hyb J01 t1, time_model). Label (me): misread (the user asks how to approach the analysis; nothing asks for a
dynamic model). There are no recorded controls, so precision is checked on three sentences I wrote, each asking for the
form outside the ask's words (`controls.json`): read by Jev for real (cost < US$0.001), not recorded sessions.

## Gates

- C0, off = no change: flags off, harness replay 0 of 1388 changed vs `replay-frozen.json`; the test suite (clean
  environment) has no new failures beyond the known env-dependent one.
- C1, precision (hard): each of the 3 written controls keeps its form reason (Jev does not doubt it).
- C2, recall: J01's condition row no longer says the time reason.
- C3, calls unchanged: flags-on harness replay changes 0 calls vs `jev-permissive-2026-10-28/replay-before.json`.
- C4, reasons: J01's new line only loses the form sentence (the rest of its old line, or layer 2); no new reason text.

Stop rule: if C1 fails, the change is withdrawn as declared. One recorded reading cannot show a rate; this is a
targeted fix for the wrong-reason rule, reported as such.
