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
  status               text not null default 'active',
  assignment_submitted boolean not null default false,
  updated_at           timestamptz not null default now(),
  unique (enrollment_id, date)
);

-- reminder_log
create table if not exists reminder_log (
  id                    uuid primary key default gen_random_uuid(),
  enrollment_id         uuid not null references enrollments(id),
  channel               text not null,
  message               text,
  sent_at               timestamptz not null default now(),
  delivery_status       text not null default 'pending',
  external_message_id   text
);

create index if not exists idx_reminder_external_id on reminder_log(external_message_id);

-- groups (WhatsApp groups managed by the system)
create table if not exists groups (
  id                   uuid primary key default gen_random_uuid(),
  whatsapp_jid         text not null unique,
  name                 text not null,
  type                 text not null, -- 'announcement' | 'proof_submission' | 'class_access' | 'community'
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
  method          text not null, -- 'momo' | 'telecel' | 'bank'
  reference       text not null, -- e.g., 'ILETS'
  proof_url       text, -- screenshot upload URL
  status          text not null default 'pending', -- 'pending' | 'verified' | 'rejected'
  verified_by     uuid references students(id), -- admin who verified
  verified_at     timestamptz,
  created_at      timestamptz not null default now()
);

create index if not exists idx_payments_student on payments(student_id);
create index if not exists idx_payments_course on payments(course_id);
create index if not exists idx_payments_status on payments(status);

-- approvals (human-in-the-loop for agent actions)
create table if not exists approvals (
  id              uuid primary key default gen_random_uuid(),
  action_type     text not null, -- 'send_message' | 'create_group' | 'add_participant' | 'send_flyer'
  content         text,
  target_group_jid text,
  target_course_id uuid references courses(id),
  metadata        jsonb,
  status          text not null default 'pending', -- 'pending' | 'approved' | 'rejected' | 'modified'
  requested_by    text not null, -- 'agent' | 'admin'
  reviewed_by     uuid references students(id), -- admin who reviewed
  reviewed_at     timestamptz,
  review_notes    text,
  created_at      timestamptz not null default now()
);

create index if not exists idx_approvals_status on approvals(status);
create index if not exists idx_approvals_course on approvals(target_course_id);

-- content_library (flyers, announcements, materials)
create table if not exists content_library (
  id              uuid primary key default gen_random_uuid(),
  type            text not null, -- 'flyer' | 'announcement' | 'material'
  title           text,
  content         text,
  image_url       text,
  course_id       uuid references courses(id),
  created_by      text not null, -- 'agent' | 'admin'
  created_at      timestamptz not null default now()
);

-- audit_log (full trail of agent/admin actions)
create table if not exists audit_log (
  id              uuid primary key default gen_random_uuid(),
  actor           text not null, -- 'agent' | 'admin' | 'system'
  action          text not null,
  entity_type     text,
  entity_id       uuid,
  details         jsonb,
  created_at      timestamptz not null default now()
);

create index if not exists idx_audit_log_actor on audit_log(actor);
create index if not exists idx_audit_log_entity on audit_log(entity_type, entity_id);

create index if not exists idx_enrollments_status on enrollments(status);
create index if not exists idx_reminder_enrollment on reminder_log(enrollment_id);
create index if not exists idx_reminder_sent_at on reminder_log(sent_at);
create index if not exists idx_groups_jid on groups(whatsapp_jid);
create index if not exists idx_groups_course on groups(course_id);
