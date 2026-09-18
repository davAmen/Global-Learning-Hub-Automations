# AGENTS.md
### Instructions for any AI coding agent working in this repository

Read this file, `ARCHITECTURE.md`, and `DECISIONS.md` in full before writing or changing any code. These three files are the source of truth for this project -- not assumptions, not "best practice," not what a similar project usually looks like.

---

## 1. What This Project Is

A daily automation that sends class reminders to students and reports engagement to the administrator (David). It is the FIRST of several planned automations for a larger learning-hub operation -- but only this one is being built right now.

**The person directing you is non-technical.** He is learning by doing this with your help -- do not assume he understands infrastructure, APIs, or code unless he demonstrates it in the conversation. Explain briefly what you're doing and why when it isn't obvious, but do not lecture at length unprompted.

---

## 2. Hard Scope Boundary -- Read This Before Building Anything

**In scope for this build:**
- Student, course, and enrollment data in Supabase (see `ARCHITECTURE.md` for schema)
- A daily scheduled job that determines who needs a reminder
- Sending that reminder through exactly ONE delivery channel (WhatsApp active, Telegram backup)
- A daily report of engagement, sent to the administrator
- A simple Next.js frontend that displays this data and can manually trigger the job -- nothing more

**Out of scope -- do not build, scaffold, or suggest these:**
- A second or third delivery channel as active (Telegram is the only backup)
- Engagement scoring beyond three simple states: active / low_engagement / needs_followup
- Any editing/write screens in the frontend beyond the single "run job now" button
- A polished or styled admin UI/dashboard -- functional and plain is correct
- Student onboarding automation, course detection, AI assistant features, or anything else from later phases
- Any new third-party service, library, or architectural pattern not already named in `ARCHITECTURE.md`

**If a task seems to require going outside this list, stop and say so explicitly instead of proceeding.**

---

## 3. Do Not Re-Decide What's Already Decided

`DECISIONS.md` contains choices that were made deliberately, often after ruling out alternatives. Do not silently reopen these unless the human operator explicitly asks you to reconsider one. If you think a past decision is wrong, say so and explain why -- don't just build the alternative.

---

## 4. Non-Negotiable Engineering Rules

- **Idempotency:** the daily job must never send a duplicate reminder if run twice in the same day. Check `reminder_log` for an existing send before sending again.
- **Logging:** every send attempt (success or failure) must be logged, both to the log file and to `reminder_log`. Silent failures are not acceptable.
- **Rate limiting:** when sending to multiple students, add delays between sends. Do not blast all messages simultaneously.
- **Secrets:** never hardcode an API key, password, or credential anywhere in code. Always read from environment variables via `.env`. Never write a real key into `.env.example` -- only placeholder text.
- **No real student data before explicit authorization:** use `scripts/seed_sample_data.py` and fake data until the human operator explicitly says the controlled pilot (Week 3) has started.
- **Small, scoped commits:** one logical change per commit, with a message explaining what and why.
- **Do not refactor code you weren't asked to touch**, even if you notice something you'd do differently. Flag it instead.

---

## 5. Code Conventions

- Python: type hints on function signatures, docstrings on anything non-trivial, small functions over large ones.
- Follow the file/folder structure in `ARCHITECTURE.md` exactly.
- Every new piece of automation logic needs a corresponding test in `tests/`.
- Prefer explicit, readable code over clever code.

---

## 6. When Uncertain

Ask, don't guess. Specifically ask when:
- A request seems to require a new library, service, or architectural change
- Real student data or a live send is about to happen and you're not sure it's authorized
- The instruction is ambiguous enough that two reasonable implementations would look very different
- Something in `DECISIONS.md` or `ARCHITECTURE.md` seems to conflict with what's being asked

Getting this wrong by proceeding silently costs more time than a clarifying question does.
