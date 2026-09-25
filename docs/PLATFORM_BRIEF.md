# Global Learning Hub: expanded product and engineering brief

## Build mandate
Audit the existing FastAPI, Supabase, scheduling, channel, and test code. Fix reproducible defects and security weaknesses; add meaningful tests and CI. Preserve the functioning reminder system. Build a responsive public website and learner portal with accessible, low-bandwidth course discovery and enrollment. Deliver usable features in verifiable stages; never claim the platform is bug-free or superior to every competitor without evidence.

## Audience and value
Start with Ghana and expand across Africa. Offer practical job and entrepreneurship skills at accessible prices, with local context, mobile-first access, transcripts, captions, downloadable low-bandwidth lessons, and learner-selected language where quality has been reviewed. Support English and selected local languages incrementally; track translator and tutor review. Clarify that learning certificates are platform certificates, not accredited qualifications unless accreditation is obtained.

## Product journeys
1. A prospect explores a transparent course catalog, sees prerequisites, outcomes, language, duration, tutor format, accessibility options, exact USD price, and any tax, exchange rate, or processor fee before payment.
2. The learner registers, chooses AI tutor or a scheduled human tutor if available, and requests a place. The $1 seat reservation is a separate, clearly disclosed payment. Show its refund and credit policy before checkout. A signed provider webhook verifies payment before a seat is reserved or a downloadable, verifiable admission letter is issued. Never trust a browser redirect as payment proof.
3. Course prices are set per offering from $2 to $50 USD; distinguish total course fee from the $1 reservation, and disclose whether the reservation is credited. Provide locally supported payment methods where the selected provider permits, while showing actual local currency conversion before authorization.
4. Learners use a dashboard for lessons, progress, feedback, tutor bookings, receipts, and admission letters. Access to paid lessons depends on verified entitlements. Provide support and refund requests.
5. Collect daily opt-in feedback from learners and prospects. An AI assistant categorizes and summarizes it, proposes changes, and flags urgent issues. A human operator approves changes to courses, policies, pricing, or messages; maintain an audit trail and privacy controls.
6. The course assistant researches permissioned and cited sources, creates original outlines, scripts, exercises, captions, and audio/video production briefs. Subject experts review factual accuracy, copyright, accessibility, and translation before publication. Never scrape and republish third-party courses.
7. Human tutors apply via a public listing only after an operator approves vacancies and budget. Verify skills, safeguarding requirements where applicable, and payout terms. AI tutor must disclose its limitations and offer escalation to a person.

## Engineering acceptance gates
- Role-based access for learner, tutor, content reviewer, support, and administrator; server-side authorization and row-level data protection in Supabase.
- Payment provider adapter, webhook signature verification, event deduplication, persistent order state, refunds/reconciliation, and tests for retries and forged callbacks.
- Admission letter generated from a verified reservation with a unique verification code; capacity reserved transactionally and expired holds released.
- Feedback queue with consent, retention, moderation, prompt-injection resistance, human approval, and measurable outcomes.
- Course content with provenance/license metadata, review status, language variants, captions, transcripts, and mobile/low-bandwidth checks.
- Security review, rate limits, audit logs, error monitoring, automated tests, accessibility checks, and a controlled pilot using synthetic data first.

## Delivery sequence
1. Repair and secure the existing reminder service, align configuration and documentation, run CI.
2. Public site and read-only catalog with tested mobile layouts; register/login and protected learner profile.
3. Verified $1 reservation and $2–$50 course checkout, admission letter, receipts, entitlements, and refunds.
4. Reviewed lessons, AI tutor, human tutor booking, and multilingual accessibility.
5. Feedback assistant and reviewed course-authoring workflow; tutor hiring tools after an approved budget.

## Decisions needed before live commerce
Business entity and merchant account; eligible payment methods and countries; reservation credit/refund policy; tax treatment and prices; legal age and privacy terms; initial courses and licensed source material; human tutor compensation; languages and review capacity. Until these are set, keep all commerce and admissions in a non-live environment.

## Competitive reference, checked 2026-09-25
Coursera offers online courses with optional financial aid for some programs; Alison permits free course learning with optional paid certificates. Neither observation establishes that a new platform can surpass them. Differentiate through accessible local examples, affordable transparent prices, multilingual review, and real support; validate with a Ghana pilot before claiming comparative outcomes.
