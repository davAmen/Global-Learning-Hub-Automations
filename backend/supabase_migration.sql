-- Run this in Supabase Dashboard → SQL Editor → New Query → Run
-- This migration adds new tables and modifies existing ones for Phase 1+

-- 1. Update courses table with new columns
alter table courses add column if not exists timezone text not null default 'GMT';
alter table courses add column if not exists is_active boolean not null default true;

-- 2. Update enrollments with status check constraint and unique
alter table enrollments add column if not exists status text not null default 'active';
alter table enrollments drop constraint if exists enrollments_status_check;
alter table enrollments add constraint enrollments_status_check check (status in ('active', 'inactive', 'completed', 'dropped'));
alter table enrollments add constraint enrollments_student_course_unique unique (student_id, course_id);

-- 3. Update engagement_log with status check and unique
alter table engagement_log add constraint if not exists engagement_log_status_check check (status in ('active', 'low_engagement', 'needs_followup'));
alter table engagement_log add constraint if not exists engagement_log_unique unique (enrollment_id, date);

-- 4. Update reminder_log - polymorphic reference (enrollment OR course)
alter table reminder_log add column if not exists course_id uuid references courses(id) on delete set null;
alter table reminder_log add column if not exists metadata jsonb;
alter table reminder_log add column if not exists delivery_status text not null default 'pending';
alter table reminder_log drop constraint if exists reminder_log_delivery_status_check;
alter table reminder_log add constraint reminder_log_delivery_status_check check (delivery_status in ('pending', 'sent', 'failed', 'delivered', 'read'));
-- Make enrollment_id nullable for group messages
alter table reminder_log alter column enrollment_id drop not null;
-- Add polymorphic constraint
alter table reminder_log drop constraint if exists reminder_log_polymorphic_check;
alter table reminder_log add constraint reminder_log_polymorphic_check check (
    (enrollment_id is not null and course_id is null) or
    (enrollment_id is null and course_id is not null) or
    (enrollment_id is not null and course_id is not null)
);

create index if not exists idx_reminder_course on reminder_log(course_id);

-- 5. Create groups table
create table if not exists groups (
  id                   uuid primary key default gen_random_uuid(),
  whatsapp_jid         text not null unique,
  name                 text not null,
  type                 text not null check (type in ('announcement', 'proof_submission', 'class_access', 'community')),
  course_id            uuid references courses(id) on delete set null,
  parent_community_jid text,
  is_active            boolean not null default true,
  settings             jsonb,
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now()
);

create index if not exists idx_groups_jid on groups(whatsapp_jid);
create index if not exists idx_groups_course on groups(course_id);

-- 6. Create payments table
create table if not exists payments (
  id              uuid primary key default gen_random_uuid(),
  student_id      uuid not null references students(id) on delete cascade,
  course_id       uuid not null references courses(id) on delete cascade,
  amount          decimal(10,2) not null check (amount > 0),
  currency        text not null default 'GHS' check (currency in ('GHS', 'USD', 'EUR')),
  method          text not null check (method in ('momo', 'telecel', 'bank', 'card', 'cash')),
  reference       text not null,
  proof_url       text,
  status          text not null default 'pending' check (status in ('pending', 'verified', 'rejected', 'refunded')),
  verified_by     uuid references students(id) on delete set null,
  verified_at     timestamptz,
  rejected_by     uuid references students(id) on delete set null,
  rejected_at     timestamptz,
  rejection_reason text,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index if not exists idx_payments_student on payments(student_id);
create index if not exists idx_payments_course on payments(course_id);
create index if not exists idx_payments_status on payments(status);
create index if not exists idx_payments_reference on payments(reference);

-- 7. Create approvals table
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

-- 8. Create content_library table
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

-- 9. Create audit_log table
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

-- 10. Create system_config table
create table if not exists system_config (
  key         text primary key,
  value       jsonb not null,
  description text,
  updated_at  timestamptz not null default now(),
  updated_by  text
);

-- 11. Update existing tables with missing indexes
create index if not exists idx_enrollments_status on enrollments(status);
create index if not exists idx_enrollments_student on enrollments(student_id);
create index if not exists idx_enrollments_course on enrollments(course_id);

create index if not exists idx_reminder_external_id on reminder_log(external_message_id);
create index if not exists idx_reminder_enrollment on reminder_log(enrollment_id);
create index if not exists idx_reminder_course on reminder_log(course_id);
create index if not exists idx_reminder_sent_at on reminder_log(sent_at);