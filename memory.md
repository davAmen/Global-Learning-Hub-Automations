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
