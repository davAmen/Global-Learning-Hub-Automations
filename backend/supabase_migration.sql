-- Run this in Supabase Dashboard → SQL Editor → New Query → Run

-- groups (WhatsApp groups managed by the system)
create table if not exists groups (
  id                   uuid primary key default gen_random_uuid(),
  whatsapp_jid         text not null unique,
  name                 text not null,
  type                 text not null,
  course_id            uuid references courses(id),
  parent_community_jid text,
  is_active            boolean not null default true,
  created_at           timestamptz not null default now()
);

-- payments (student course payments)
create table if not exists payments (
  id              uuid primary key default gen_random_uuid(),
  student_id      uuid not null references students(id),
  course_id       uuid not null references courses(id),
  amount          decimal(10,2) not null,
  currency        text not null default 'GHS',
  method          text not null,
  reference       text not null,
  proof_url       text,
  status          text not null default 'pending',
  verified_by     uuid references students(id),
  verified_at     timestamptz,
  created_at      timestamptz not null default now()
);

create index if not exists idx_payments_student on payments(student_id);
create index if not exists idx_payments_course on payments(course_id);
create index if not exists idx_payments_status on payments(status);

-- approvals (human-in-the-loop for agent actions)
create table if not exists approvals (
  id              uuid primary key default gen_random_uuid(),
  action_type     text not null,
  content         text,
  target_group_jid text,
  target_course_id uuid references courses(id),
  metadata        jsonb,
  status          text not null default 'pending',
  requested_by    text not null,
  reviewed_by     uuid references students(id),
  reviewed_at     timestamptz,
  review_notes    text,
  created_at      timestamptz not null default now()
);

create index if not exists idx_approvals_status on approvals(status);
create index if not exists idx_approvals_course on approvals(target_course_id);

-- content_library (flyers, announcements, materials)
create table if not exists content_library (
  id              uuid primary key default gen_random_uuid(),
  type            text not null,
  title           text,
  content         text,
  image_url       text,
  course_id       uuid references courses(id),
  created_by      text not null,
  created_at      timestamptz not null default now()
);

-- audit_log (full trail of agent/admin actions)
create table if not exists audit_log (
  id              uuid primary key default gen_random_uuid(),
  actor           text not null,
  action          text not null,
  entity_type     text,
  entity_id       uuid,
  details         jsonb,
  created_at      timestamptz not null default now()
);

create index if not exists idx_audit_log_actor on audit_log(actor);
create index if not exists idx_audit_log_entity on audit_log(entity_type, entity_id);

-- Additional indexes
create index if not exists idx_groups_jid on groups(whatsapp_jid);
create index if not exists idx_groups_course on groups(course_id);