-- students
create table if not exists students (
  id                  uuid primary key default gen_random_uuid(),
  name                text not null,
  phone               text,
  email               text,
  password_hash       text,
  email_verified      boolean not null default false,
  role                text not null default 'learner' check (role in ('learner', 'admin', 'instructor')),
  last_login_at       timestamptz,
  failed_login_attempts integer not null default 0,
  locked_until        timestamptz,
  created_at          timestamptz not null default now()
);

create index if not exists idx_students_email on students(email);
create index if not exists idx_students_role on students(role);

-- courses
create table if not exists courses (
  id                       uuid primary key default gen_random_uuid(),
  name                     text not null,
  start_date               date,
  class_time               time,
  timezone                 text not null default 'GMT',
  is_active                boolean not null default true,
  price_minor              integer not null default 0,
  currency                 text not null default 'GHS' check (currency in ('GHS', 'USD', 'EUR')),
  capacity                 integer,
  seat_reservation_minor   integer not null default 0,
  description              text,
  learning_outcomes        text[],
  prerequisites            text[],
  expected_study_hours     integer,
  support_email            text,
  support_phone            text,
  whatsapp_group_jid       text,
  proof_submission_group_jid text,
  created_at               timestamptz not null default now()
);

-- enrollments
create table if not exists enrollments (
  id          uuid primary key default gen_random_uuid(),
  student_id  uuid not null references students(id) on delete cascade,
  course_id   uuid not null references courses(id) on delete cascade,
  status      text not null default 'active' check (status in ('active', 'inactive', 'completed', 'dropped')),
  enrolled_at timestamptz not null default now(),
  unique (student_id, course_id)
);

-- engagement_log
create table if not exists engagement_log (
  id                   uuid primary key default gen_random_uuid(),
  enrollment_id        uuid not null references enrollments(id) on delete cascade,
  date                 date not null,
  status               text not null default 'active' check (status in ('active', 'low_engagement', 'needs_followup')),
  assignment_submitted boolean not null default false,
  updated_at           timestamptz not null default now(),
  unique (enrollment_id, date)
);

-- reminder_log
-- Polymorphic reference: can reference either enrollments (individual) or courses (group)
create table if not exists reminder_log (
  id                    uuid primary key default gen_random_uuid(),
  enrollment_id         uuid references enrollments(id) on delete set null,
  course_id             uuid references courses(id) on delete set null,
  channel               text not null,
  message               text not null,
  sent_at               timestamptz not null default now(),
  delivery_status       text not null default 'pending' check (delivery_status in ('pending', 'sent', 'failed', 'delivered', 'read')),
  external_message_id   text,
  metadata              jsonb,
  check (
    (enrollment_id is not null and course_id is null) or
    (enrollment_id is null and course_id is not null) or
    (enrollment_id is not null and course_id is not null)
  )
);

-- groups (WhatsApp groups managed by the system)
create table if not exists groups (
  id                   uuid primary key default gen_random_uuid(),
  whatsapp_jid         text not null unique,
  name                 text not null,
  type                 text not null check (type in ('announcement', 'proof_submission', 'class_access', 'community', 'class')),
  course_id            uuid references courses(id) on delete set null,
  parent_community_jid text,
  is_active            boolean not null default true,
  settings             jsonb,
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now()
);

create index if not exists idx_groups_jid on groups(whatsapp_jid);
create index if not exists idx_groups_course on groups(course_id);

-- payments (student course payments)
create table if not exists payments (
  id                      uuid primary key default gen_random_uuid(),
  student_id              uuid not null references students(id) on delete cascade,
  course_id               uuid not null references courses(id) on delete cascade,
  amount                  decimal(10,2) not null check (amount > 0),
  currency                text not null default 'GHS' check (currency in ('GHS', 'USD', 'EUR')),
  method                  text not null check (method in ('momo', 'telecel', 'bank', 'card', 'cash')),
  reference               text not null,
  proof_url               text,
  status                  text not null default 'pending' check (status in ('pending', 'verified', 'rejected', 'refunded')),
  verified_by             uuid references students(id) on delete set null,
  verified_at             timestamptz,
  rejected_by             uuid references students(id) on delete set null,
  rejected_at             timestamptz,
  rejection_reason        text,
  provider                text check (provider in ('paystack', 'seefcash', 'manual_momo', 'manual_telecel')),
  provider_payment_id     text,
  provider_reference      text,
  provider_fees_minor     integer,
  provider_response       jsonb,
  seat_reservation        boolean not null default false,
  seat_reservation_verified_at timestamptz,
  enrollment_created      boolean not null default false,
  created_at              timestamptz not null default now(),
  updated_at              timestamptz not null default now()
);

create index if not exists idx_payments_student on payments(student_id);
create index if not exists idx_payments_course on payments(course_id);
create index if not exists idx_payments_status on payments(status);
create index if not exists idx_payments_reference on payments(reference);
create index if not exists idx_payments_provider on payments(provider);
create index if not exists idx_payments_provider_payment_id on payments(provider_payment_id);

-- approvals (human-in-the-loop for agent actions)
create table if not exists approvals (
  id              uuid primary key default gen_random_uuid(),
  action_type     text not null check (action_type in ('send_message', 'create_group', 'add_participant', 'send_flyer', 'verify_payment', 'broadcast')),
  content         text,
  target_group_jid text,
  target_course_id uuid references courses(id) on delete set null,
  metadata        jsonb,
  status          text not null default 'pending' check (status in ('pending', 'approved', 'rejected', 'modified', 'cancelled')),
  requested_by    text not null check (requested_by in ('agent', 'admin', 'system')),
  reviewed_by     uuid references students(id) on delete set null,
  reviewed_at     timestamptz,
  review_notes    text,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index if not exists idx_approvals_status on approvals(status);
create index if not exists idx_approvals_course on approvals(target_course_id);
create index if not exists idx_approvals_type on approvals(action_type);

-- content_library (flyers, announcements, materials)
create table if not exists content_library (
  id              uuid primary key default gen_random_uuid(),
  type            text not null check (type in ('flyer', 'announcement', 'material', 'template')),
  title           text,
  content         text,
  image_url       text,
  course_id       uuid references courses(id) on delete set null,
  created_by      text not null check (created_by in ('agent', 'admin', 'system')),
  version         int not null default 1,
  is_active       boolean not null default true,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index if not exists idx_content_course on content_library(course_id);

-- audit_log (full trail of agent/admin actions)
create table if not exists audit_log (
  id              uuid primary key default gen_random_uuid(),
  actor           text not null check (actor in ('agent', 'admin', 'system', 'user')),
  action          text not null,
  entity_type     text,
  entity_id       uuid,
  details         jsonb,
  ip_address      inet,
  user_agent      text,
  created_at      timestamptz not null default now()
);

create index if not exists idx_audit_log_actor on audit_log(actor);
create index if not exists idx_audit_log_entity on audit_log(entity_type, entity_id);
create index if not exists idx_audit_log_created on audit_log(created_at);

-- system_config (key-value configuration)
create table if not exists system_config (
  key         text primary key,
  value       jsonb not null,
  description text,
  updated_at  timestamptz not null default now(),
  updated_by  text
);

-- indexes for existing tables
create index if not exists idx_enrollments_status on enrollments(status);
create index if not exists idx_enrollments_student on enrollments(student_id);
create index if not exists idx_enrollments_course on enrollments(course_id);

create index if not exists idx_reminder_external_id on reminder_log(external_message_id);
create index if not exists idx_reminder_enrollment on reminder_log(enrollment_id);
create index if not exists idx_reminder_course on reminder_log(course_id);
create index if not exists idx_reminder_sent_at on reminder_log(sent_at);