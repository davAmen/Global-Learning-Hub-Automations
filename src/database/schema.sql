-- students
create table if not exists students (
  id         uuid primary key default gen_random_uuid(),
  name       text not null,
  phone      text,
  email      text,
  created_at timestamptz not null default now()
);

-- courses
create table if not exists courses (
  id         uuid primary key default gen_random_uuid(),
  name       text not null,
  start_date date,
  class_time time,
  created_at timestamptz not null default now()
);

-- enrollments
create table if not exists enrollments (
  id          uuid primary key default gen_random_uuid(),
  student_id  uuid not null references students(id),
  course_id   uuid not null references courses(id),
  status      text not null default 'active',
  enrolled_at timestamptz not null default now()
);

-- engagement_log
create table if not exists engagement_log (
  id                   uuid primary key default gen_random_uuid(),
  enrollment_id        uuid not null references enrollments(id),
  date                 date not null,
  status               text not null default 'active'
                       check (status in ('active', 'low_engagement', 'needs_followup')),
  assignment_submitted boolean not null default false,
  updated_at           timestamptz not null default now(),
  unique (enrollment_id, date)
);

-- reminder_log
create table if not exists reminder_log (
  id              uuid primary key default gen_random_uuid(),
  enrollment_id   uuid references enrollments(id),
  channel         text not null,
  message         text,
  idempotency_key text unique,
  sent_at         timestamptz not null default now(),
  delivery_status text not null default 'pending'
);

create index if not exists idx_enrollments_status on enrollments(status);
create index if not exists idx_reminder_enrollment on reminder_log(enrollment_id);
create index if not exists idx_reminder_sent_at on reminder_log(sent_at);

-- Phase 2: trusted mapping from Supabase Auth users to application roles.
-- Profile rows are provisioned by a trusted operator, never by these API routes.
create table if not exists app_user_profiles (
  auth_user_id uuid primary key references auth.users(id) on delete cascade,
  role         text not null check (role in ('staff', 'learner')),
  student_id   uuid unique references students(id),
  created_at   timestamptz not null default now(),
  check (
    (role = 'staff' and student_id is null)
    or (role = 'learner' and student_id is not null)
  )
);

-- Phase 2 weekly device-readiness notice: append-only payment audit events.
create table if not exists enrollment_payment_verification_events (
  id            bigint generated always as identity primary key,
  enrollment_id uuid not null references enrollments(id),
  action        text not null check (action in ('verified', 'revoked')),
  recorded_by   uuid not null,
  recorded_at   timestamptz not null default clock_timestamp()
);

create index if not exists idx_payment_verification_enrollment_latest
  on enrollment_payment_verification_events(enrollment_id, id desc);

-- Consent is separate for each student, purpose, and channel.
create table if not exists student_channel_consent_events (
  id              bigint generated always as identity primary key,
  student_id      uuid not null references students(id),
  purpose         text not null check (purpose = 'device_readiness_weekly'),
  channel         text not null check (channel <> '' and channel = lower(btrim(channel))),
  action          text not null check (action in ('opt_in', 'opt_out')),
  consent_version text,
  source          text not null check (source in ('learner_self_service', 'learner_direct_request')),
  recorded_by     uuid not null,
  recorded_at     timestamptz not null default clock_timestamp(),
  check (
    action = 'opt_out'
    or (consent_version is not null and length(btrim(consent_version)) > 0)
  )
);

create index if not exists idx_channel_consent_latest
  on student_channel_consent_events(student_id, purpose, channel, id desc);

-- Each row is a full preferred/fallback order snapshot, separate from consent.
create table if not exists student_channel_preference_events (
  id            bigint generated always as identity primary key,
  student_id    uuid not null references students(id),
  purpose       text not null check (purpose = 'device_readiness_weekly'),
  channel_order text[] not null default '{}'::text[] check (cardinality(channel_order) <= 16),
  recorded_by   uuid not null,
  recorded_at   timestamptz not null default clock_timestamp()
);

create index if not exists idx_channel_preference_latest
  on student_channel_preference_events(student_id, purpose, id desc);

-- These logs are server-only and append-only for the application role.
alter table app_user_profiles enable row level security;
alter table enrollment_payment_verification_events enable row level security;
alter table student_channel_consent_events enable row level security;
alter table student_channel_preference_events enable row level security;

revoke all on table app_user_profiles from public, anon, authenticated, service_role;
revoke all on table enrollment_payment_verification_events from public, anon, authenticated, service_role;
revoke all on table student_channel_consent_events from public, anon, authenticated, service_role;
revoke all on table student_channel_preference_events from public, anon, authenticated, service_role;
revoke all on sequence enrollment_payment_verification_events_id_seq from public, anon, authenticated, service_role;
revoke all on sequence student_channel_consent_events_id_seq from public, anon, authenticated, service_role;
revoke all on sequence student_channel_preference_events_id_seq from public, anon, authenticated, service_role;
grant select on table app_user_profiles to service_role;
grant select, insert on table enrollment_payment_verification_events to service_role;
grant select, insert on table student_channel_consent_events to service_role;
grant select, insert on table student_channel_preference_events to service_role;
grant usage, select on sequence enrollment_payment_verification_events_id_seq to service_role;
grant usage, select on sequence student_channel_consent_events_id_seq to service_role;
grant usage, select on sequence student_channel_preference_events_id_seq to service_role;
