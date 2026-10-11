# AGENTS.md
### Instructions for any AI coding agent (Claude Code, or otherwise) working in this repository


---

## Behavioral Guidelines (Karpathy Rules — Always Active)

### 1. Think Before Coding
**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before writing a single line:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First
**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes
**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Do not "improve" adjacent code, comments, or formatting.
- Do not refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Do not remove pre-existing dead code unless explicitly asked.

The test: Every changed line must trace directly to the current task.

### 4. Goal-Driven Execution
**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"

For multi-step tasks, state a brief plan before starting:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

---

## Scope Control — Stay in Your Lane

Only modify files, functions, and lines directly related to the current task.
Do not refactor, rename, reorganize, reformat, or "improve" anything not explicitly asked for.
If you notice something worth fixing elsewhere, leave a note. Do not touch it.

---

## Destructive Actions — Full Stop

Before deleting any file, overwriting existing code, dropping database records,
or removing dependencies — stop completely. List exactly what will be affected.
Ask for explicit confirmation. Only proceed after Evans says yes in the current message.

---

## Hard Stops — These Never Happen Without Explicit Permission

The following require explicit in-session confirmation, no exceptions:
- Deploying or pushing to any environment (staging, production, etc.)
- Running migrations or schema changes on any database
- Sending any email, message, or external API call to real recipients
- Executing any command with irreversible external side effects

"You mentioned this earlier" is not confirmation. Confirmation must be in the current message.

---

Maintain a file called MEMORY.md. After any significant decision, about direction, format, content, approach, or strategy, add an entry:

## [Date], [Decision]
**What was decided:** [the choice made]
**Why:** [the reasoning]
**What was rejected:** [alternatives considered and why they were ruled out]

Read MEMORY.md at the start of every session before doing anything. Never contradict a logged decision without flagging it first.

## After Every Task — Status Report

After completing any coding task, always end with:
- **Files changed:** [list every file touched]
- **What was modified:** [one line per file]
- **Files intentionally not touched:** [if relevant]
- **Follow-up needed:** [anything requiring a decision or attention]

Keep it short. This is a status update, not a recap.

---


Read this file, `ARCHITECTURE.md`, and `DECISIONS.md` in full before writing or changing any code. These three files are the source of truth for this project — not assumptions, not "best practice," not what a similar project usually looks like.

If you are Claude Code specifically and this repo also has a `CLAUDE.md`, treat it as identical to this file — they should never conflict. If only one exists, copy it to the other name so every tool reads the same rules.

---

## 1. What This Project Is

A daily automation that sends class reminders to students and reports engagement to the administrator (David). It is the FIRST of several planned automations for a larger learning-hub operation — but only this one is being built right now.

**The person directing you is non-technical.** He is learning by doing this with your help — do not assume he understands infrastructure, APIs, or code unless he demonstrates it in the conversation. Explain briefly what you're doing and why when it isn't obvious, but do not lecture at length unprompted.

---

## 2. Hard Scope Boundary — Read This Before Building Anything

**In scope for this build:**
- Student, course, and enrollment data in Supabase (see `ARCHITECTURE.md` for schema)
- A daily scheduled job that determines who needs a reminder
- Sending that reminder through exactly ONE delivery channel (see `DECISIONS.md` for which one)
- A daily report of engagement, sent to the administrator
- A simple Next.js frontend that displays this data and can manually trigger the job — nothing more

**Out of scope — do not build, scaffold, or suggest these, even if they seem like natural next steps:**
- A second or third delivery channel (the architecture supports adding them later — do not add them now)
- Engagement scoring beyond three simple states: active / low_engagement / needs_followup
- Any editing/write screens in the frontend beyond the single "run job now" button
- A polished or styled admin UI/dashboard — functional and plain is correct
- Student onboarding automation, course detection, AI assistant features, or anything else from later phases of the original project document
- Any new third-party service, library, or architectural pattern not already named in `ARCHITECTURE.md`

**If a task seems to require going outside this list, stop and say so explicitly instead of proceeding.** Do not quietly expand scope because it seemed like a small addition or because you generated something useful along the way.

---

## 3. Do Not Re-Decide What's Already Decided

`DECISIONS.md` contains choices that were made deliberately, often after ruling out alternatives. Do not silently reopen these (e.g. suggesting Google Sheets as a data store, or defaulting to a different channel or framework) unless the human operator explicitly asks you to reconsider one. If you think a past decision is wrong, say so and explain why — don't just build the alternative.

---

## 4. Non-Negotiable Engineering Rules

- **Idempotency:** the daily job must never send a duplicate reminder if run twice in the same day. Check `reminder_log` for an existing send before sending again.
- **Logging:** every send attempt (success or failure) must be logged, both to the log file and to `reminder_log`. Silent failures are not acceptable.
- **Rate limiting:** when sending to multiple students, add delays between sends. Do not blast all messages simultaneously — this risks the delivery account being throttled or banned.
- **Secrets:** never hardcode an API key, password, or credential anywhere in code. Always read from environment variables via `.env`. Never write a real key into `.env.example` — only placeholder text.
- **No real student data before explicit authorization:** use `scripts/seed_sample_data.py` and fake data until the human operator explicitly says the controlled pilot (Week 3) has started. If you are unsure whether real data is authorized yet, ask.
- **Small, scoped commits:** one logical change per commit, with a message explaining what and why. Do not bundle unrelated changes together.
- **Do not refactor code you weren't asked to touch**, even if you notice something you'd do differently. Flag it instead.

---

## 5. Code Conventions

- Python: type hints on function signatures, docstrings on anything non-trivial, small functions over large ones.
- Follow the file/folder structure in `ARCHITECTURE.md` exactly — new files go where that document says they go. If something doesn't fit the existing structure, flag it rather than inventing a new folder pattern.
- Every new piece of automation logic (scheduler, engagement rules, channel sending) needs a corresponding test in `tests/`, even a simple one.
- Prefer explicit, readable code over clever code. This project will be read and modified by a non-technical person with a mentor, not by expert engineers — optimize for that audience.

---

## 6. When Uncertain

Ask, don't guess. Specifically ask when:
- A request seems to require a new library, service, or architectural change
- Real student data or a live send is about to happen and you're not sure it's authorized
- The instruction is ambiguous enough that two reasonable implementations would look very different
- Something in `DECISIONS.md` or `ARCHITECTURE.md` seems to conflict with what's being asked

Getting this wrong by proceeding silently costs more time than a clarifying question does.


---
Create a well detailed explanation of every major new feature you create insdie docs/ folder
----