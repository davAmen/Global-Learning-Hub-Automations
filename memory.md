# Project memory

## 2026-09-26, Reconcile through an isolated GitHub-based branch

**What was decided:** Use `reconcile/github-main`, based on the selected GitHub repository's fetched `main`, as the safe place to integrate reviewed work. Preserve the earlier local `main`; port changes selectively after review.
**Why:** The local and GitHub branches diverged and use different layouts. The GitHub branch contains newer platform/security documentation and root-level `src/`, while the local branch contains `backend/` and `frontend/`.
**What was rejected:** Force-pushing or merging the entire local tree over GitHub, which could discard remote-only work or introduce incompatible paths.

## 2026-09-26, Log administrator report delivery attempts

**What was decided:** Use `reminder_log` for administrator report attempts, with a null `enrollment_id`; keep report attempts out of student reminder counts. Update the schema file only and do not migrate Supabase without explicit authorization.
**Why:** The send-attempt logging rule applies to administrator reports too, but those messages are not associated with a learner enrollment.
**What was rejected:** Sending without an audit record, inventing an enrollment, or creating a second log table.

## 2026-09-26, Use non-routable sample recipients for local tests

**What was decided:** Seed fake students with fictional 555-01xx phone placeholders and keep provider credentials blank during local tests.
**Why:** Plausible Ghanaian phone numbers in sample data could belong to real people and a configured provider could contact them accidentally.
**What was rejected:** Keeping realistic-looking local phone numbers or telling users to add live messaging credentials before a controlled pilot.

## 2026-09-26, Phase 1 hardening handoff on the selected GitHub branch

**What was decided:** Keep the reviewed changes on local branch `reconcile/github-main`, based on the selected repository's fetched `main`; preserve the old local `main`. The branch currently includes the roadmap, reminder pre-send logging, report-attempt logging, missing WhatsApp-recipient guard, and fictional seed recipients. Latest full test run: 18 passed, 1 Starlette deprecation warning.
**Why:** These changes address auditability and accidental-contact risks while retaining GitHub-only work and the staged scope.
**What was rejected:** Pushing before current-request authorization, force-pushing/merging the divergent local tree, and applying the nullable `reminder_log.enrollment_id` change to a live Supabase database without explicit authorization.

## 2026-09-27, Phase 2 attendance check-in direction — superseded in part

**Originally decided:** Phase 2 is activated for consent-based attendance. No class platform was selected; the initial design proposed visible learner-initiated check-in after verified learner login, with auditable teacher corrections. The no-platform direction was later superseded by the owned hybrid-platform decision below; the identity and correction safeguards remain.
**Why:** The repository has no class-platform integration, learner authentication, or attendance model; accepting a student ID alone could allow impersonation.
**What was rejected:** Covert sensing, attendance inferred from online/read status, and public check-ins using an unverified student ID. Define session, attendance-status, consent, correction, and retention rules before schema/API work.

## 2026-09-27, Hybrid local and remote classroom platform selected

**What was decided:** The operator wants an owned class platform that supports local classroom use over a LAN when internet is unavailable and remote online access when connectivity exists. This supersedes WhatsApp group management as the class-platform direction; the existing WhatsApp reminder service remains unchanged.
**Why:** The operator wants teachers and learners to exchange lessons and resources locally while still enabling remote access.
**What was rejected:** A permanently isolated platform as the only mode and a WhatsApp group as the classroom platform. “Interlink” remains undefined; assume LAN/intranet until clarified. The local/cloud source of truth, offline write ownership, synchronization/conflict rules, security, backup, and attendance policies must be decided before code or schema changes.

## 2026-09-27, Local classroom hub authority selected

**What was decided:** For each site, its local hub is the authoritative record keeper for class records created there during internet outages; it syncs those records to the online service after connectivity returns.
**Why:** This allows local classes to continue and record work without internet while retaining remote access when online.
**What was rejected:** Requiring the cloud to be reachable for every classroom write, or silently letting the cloud overwrite locally authoritative records.
**Still unresolved:** Sync acknowledgements/retries, duplicate handling, event ordering, remote-origin record ownership, corrections/conflicts, local storage, and backup/restore.
