-- Run this in Supabase Dashboard → SQL Editor → New Query → Run
-- This migration adds RLS policies, course pricing, student auth fields for Phase 2+

-- ============================================================
-- 1. ADD COURSE PRICING & METADATA FIELDS
-- ============================================================
alter table courses add column if not exists price_minor integer not null default 0;  -- price in minor units (cents/pesewas)
alter table courses add column if not exists currency text not null default 'GHS' check (currency in ('GHS', 'USD', 'EUR'));
alter table courses add column if not exists capacity integer;  -- max enrollments, null = unlimited
alter table courses add column if not exists seat_reservation_minor integer not null default 0;  -- $1 equivalent in minor units
alter table courses add column if not exists description text;
alter table courses add column if not exists learning_outcomes text[];
alter table courses add column if not exists prerequisites text[];
alter table courses add column if not exists expected_study_hours integer;
alter table courses add column if not exists support_email text;
alter table courses add column if not exists support_phone text;
alter table courses add column if not exists whatsapp_group_jid text;  -- class access group
alter table courses add column if not exists proof_submission_group_jid text;  -- payment proof group

-- ============================================================
-- 2. ADD STUDENT AUTH FIELDS
-- ============================================================
alter table students add column if not exists password_hash text;
alter table students add column if not exists email_verified boolean not null default false;
alter table students add column if not exists role text not null default 'learner' check (role in ('learner', 'admin', 'instructor'));
alter table students add column if not exists last_login_at timestamptz;
alter table students add column if not exists failed_login_attempts integer not null default 0;
alter table students add column if not exists locked_until timestamptz;

create index if not exists idx_students_email on students(email);
create index if not exists idx_students_role on students(role);

-- ============================================================
-- 3. UPDATE GROUPS TYPE CONSTRAINT
-- ============================================================
alter table groups drop constraint if exists groups_type_check;
alter table groups add constraint groups_type_check check (type in ('announcement', 'proof_submission', 'class_access', 'community', 'class'));

-- ============================================================
-- 4. ADD PAYMENT PROVIDER FIELDS
-- ============================================================
alter table payments add column if not exists provider text check (provider in ('paystack', 'seefcash', 'manual_momo', 'manual_telecel'));
alter table payments add column if not exists provider_payment_id text;
alter table payments add column if not exists provider_reference text;
alter table payments add column if not exists provider_fees_minor integer;
alter table payments add column if not exists provider_response jsonb;
alter table payments add column if not exists seat_reservation boolean not null default false;
alter table payments add column if not exists seat_reservation_verified_at timestamptz;
alter table payments add column if not exists enrollment_created boolean not null default false;

create index if not exists idx_payments_provider on payments(provider);
create index if not exists idx_payments_provider_payment_id on payments(provider_payment_id);

-- ============================================================
-- 5. ENABLE RLS ON ALL TABLES
-- ============================================================
alter table students enable row level security;
alter table courses enable row level security;
alter table enrollments enable row level security;
alter table engagement_log enable row level security;
alter table reminder_log enable row level security;
alter table groups enable row level security;
alter table payments enable row level security;
alter table approvals enable row level security;
alter table content_library enable row level security;
alter table audit_log enable row level security;
alter table system_config enable row level security;

-- ============================================================
-- 6. RLS POLICIES - STUDENTS
-- ============================================================
-- Learners can read their own record
create policy "students_select_own" on students
  for select using (auth.uid() = id);

-- Learners can update their own record (limited fields)
create policy "students_update_own" on students
  for update using (auth.uid() = id)
  with check (auth.uid() = id);

-- Admins can read all students
create policy "students_select_admin" on students
  for select using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Admins can update all students
create policy "students_update_admin" on students
  for update using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Service role (backend) can do everything
create policy "students_service_role" on students
  for all using (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================
-- 7. RLS POLICIES - COURSES
-- ============================================================
-- Anyone can read active published courses (public catalogue)
create policy "courses_select_public" on courses
  for select using (is_active = true);

-- Admins can read all courses
create policy "courses_select_admin" on courses
  for select using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Admins can insert/update/delete courses
create policy "courses_write_admin" on courses
  for all using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Service role can do everything
create policy "courses_service_role" on courses
  for all using (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================
-- 8. RLS POLICIES - ENROLLMENTS
-- ============================================================
-- Learners can read their own enrollments
create policy "enrollments_select_own" on enrollments
  for select using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.id = enrollments.student_id
    )
  );

-- Learners can create enrollment for themselves (enrollment flow)
create policy "enrollments_insert_own" on enrollments
  for insert with check (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.id = enrollments.student_id
    )
  );

-- Admins can read all enrollments
create policy "enrollments_select_admin" on enrollments
  for select using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Admins can update enrollments (status changes, etc.)
create policy "enrollments_update_admin" on enrollments
  for update using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Service role can do everything
create policy "enrollments_service_role" on enrollments
  for all using (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================
-- 9. RLS POLICIES - ENGAGEMENT_LOG
-- ============================================================
-- Learners can read their own engagement
create policy "engagement_select_own" on engagement_log
  for select using (
    exists (
      select 1 from enrollments e
      join students s on s.id = e.student_id
      where e.id = engagement_log.enrollment_id
      and s.id = auth.uid()
    )
  );

-- Admins can read all engagement
create policy "engagement_select_admin" on engagement_log
  for select using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Service role can do everything
create policy "engagement_service_role" on engagement_log
  for all using (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================
-- 10. RLS POLICIES - REMINDER_LOG
-- ============================================================
-- Admins can read all reminders
create policy "reminder_select_admin" on reminder_log
  for select using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Service role can do everything
create policy "reminder_service_role" on reminder_log
  for all using (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================
-- 11. RLS POLICIES - GROUPS
-- ============================================================
-- Anyone can read active groups (for group links)
create policy "groups_select_public" on groups
  for select using (is_active = true);

-- Admins can read all groups
create policy "groups_select_admin" on groups
  for select using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Admins can manage groups
create policy "groups_write_admin" on groups
  for all using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Service role can do everything
create policy "groups_service_role" on groups
  for all using (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================
-- 12. RLS POLICIES - PAYMENTS
-- ============================================================
-- Learners can read their own payments
create policy "payments_select_own" on payments
  for select using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.id = payments.student_id
    )
  );

-- Learners can create payment records (during enrollment)
create policy "payments_insert_own" on payments
  for insert with check (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.id = payments.student_id
    )
  );

-- Admins can read all payments
create policy "payments_select_admin" on payments
  for select using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Admins can update payments (verification)
create policy "payments_update_admin" on payments
  for update using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Service role can do everything
create policy "payments_service_role" on payments
  for all using (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================
-- 13. RLS POLICIES - APPROVALS
-- ============================================================
-- Admins can read all approvals
create policy "approvals_select_admin" on approvals
  for select using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Admins can update approvals (approve/reject)
create policy "approvals_update_admin" on approvals
  for update using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Agents/System can create approvals
create policy "approvals_insert_agent" on approvals
  for insert with check (
    auth.jwt() ->> 'role' = 'service_role'
  );

-- Service role can do everything
create policy "approvals_service_role" on approvals
  for all using (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================
-- 14. RLS POLICIES - CONTENT_LIBRARY
-- ============================================================
-- Anyone can read active content for published courses
create policy "content_select_public" on content_library
  for select using (
    is_active = true
    and exists (
      select 1 from courses c
      where c.id = content_library.course_id
      and c.is_active = true
    )
  );

-- Admins can read all content
create policy "content_select_admin" on content_library
  for select using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Admins/Agents can write content
create policy "content_write_admin" on content_library
  for all using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role in ('admin', 'instructor')
    )
  );

-- Service role can do everything
create policy "content_service_role" on content_library
  for all using (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================
-- 15. RLS POLICIES - AUDIT_LOG
-- ============================================================
-- Admins can read audit logs
create policy "audit_select_admin" on audit_log
  for select using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Service role can do everything
create policy "audit_service_role" on audit_log
  for all using (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================
-- 16. RLS POLICIES - SYSTEM_CONFIG
-- ============================================================
-- Admins can read config
create policy "config_select_admin" on system_config
  for select using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Admins can update config
create policy "config_update_admin" on system_config
  for update using (
    exists (
      select 1 from students s
      where s.id = auth.uid() and s.role = 'admin'
    )
  );

-- Service role can do everything
create policy "config_service_role" on system_config
  for all using (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================
-- 17. HELPER FUNCTION FOR ADMIN CHECK
-- ============================================================
create or replace function is_admin() returns boolean
language sql security definer
as $$
  select exists (
    select 1 from students
    where id = auth.uid()
    and role = 'admin'
  );
$$;

-- ============================================================
-- 18. UPDATE EXISTING DATA DEFAULTS
-- ============================================================
-- Set default price for existing IELTS course
update courses
set price_minor = 10000,  -- GHS 100.00 in pesewas
    currency = 'GHS',
    capacity = 50,
    seat_reservation_minor = 1500,  -- GHS 15.00 (~$1)
    whatsapp_group_jid = '120363413380837553@g.us',
    proof_submission_group_jid = '120363428841556134@g.us'
where name = 'IELTS Preparation (Oct 15-30, 6-8pm GMT)'
and price_minor = 0;

-- ============================================================
-- 19. GRANT PERMISSIONS FOR AUTHENTICATED ROLE
-- ============================================================
grant select on courses to authenticated;
grant select on groups to authenticated;
grant select, insert on enrollments to authenticated;
grant select, insert on payments to authenticated;
grant select on content_library to authenticated;

grant all on students to service_role;
grant all on courses to service_role;
grant all on enrollments to service_role;
grant all on engagement_log to service_role;
grant all on reminder_log to service_role;
grant all on groups to service_role;
grant all on payments to service_role;
grant all on approvals to service_role;
grant all on content_library to service_role;
grant all on audit_log to service_role;
grant all on system_config to service_role;