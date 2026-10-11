-- DISABLE RLS entirely for development
-- Run this in Supabase SQL Editor

-- Drop existing policies first
DROP POLICY IF EXISTS "Allow all on students" ON students;
DROP POLICY IF EXISTS "Allow all on courses" ON courses;
DROP POLICY IF EXISTS "Allow all on enrollments" ON enrollments;
DROP POLICY IF EXISTS "Allow all on engagement_log" ON engagement_log;
DROP POLICY IF EXISTS "Allow all on reminder_log" ON reminder_log;

-- Disable RLS on all tables
ALTER TABLE students DISABLE ROW LEVEL SECURITY;
ALTER TABLE courses DISABLE ROW LEVEL SECURITY;
ALTER TABLE enrollments DISABLE ROW LEVEL SECURITY;
ALTER TABLE engagement_log DISABLE ROW LEVEL SECURITY;
ALTER TABLE reminder_log DISABLE ROW LEVEL SECURITY;
