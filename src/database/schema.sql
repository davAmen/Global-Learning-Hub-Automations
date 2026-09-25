-- Global Learning Hub Phase 1 schema.
create table if not exists students (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  phone text,
  email text,
  created_at timestamptz not null default now()
);

create table if not exists courses (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  start_date date,
  class_time time,
  created_at timestamptz not null default now()
);

create table if not exists enrollments (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references students(id) on delete cascade,
  course_id uuid not null references courses(id) on delete cascade,
  status text not null default 'active' check (status in ('active', 'inactive')),
  enrolled_at timestamptz not null default now()
);

create table if not exists engagement_log (
  id uuid primary key default gen_random_uuid(),
  enrollment_id uuid not null references enrollments(id) on delete cascade,
  date date not null,
  status text not null default 'active'
    check (status in ('active', 'low_engagement', 'needs_followup')),
  assignment_submitted boolean not null default false,
  updated_at timestamptz not null default now(),
  unique (enrollment_id, date)
);

create table if not exists reminder_log (
  id uuid primary key default gen_random_uuid(),
  enrollment_id uuid not null references enrollments(id) on delete cascade,
  channel text not null check (channel in ('whatsapp', 'telegram', 'email', 'sms')),
  message text,
  sent_at timestamptz not null default now(),
  delivery_status text not null default 'pending'
    check (delivery_status in ('sent', 'failed', 'pending'))
);

create index if not exists idx_enrollments_status on enrollments(status);
create index if not exists idx_enrollments_course on enrollments(course_id);
create index if not exists idx_engagement_enrollment_date on engagement_log(enrollment_id, date);
create index if not exists idx_reminder_enrollment on reminder_log(enrollment_id);
create index if not exists idx_reminder_sent_at on reminder_log(sent_at);

-- Final idempotency guard: one automated reminder attempt per enrollment per UTC day.
create unique index if not exists uq_reminder_enrollment_utc_day
on reminder_log (enrollment_id, ((sent_at at time zone 'UTC')::date));
