-- Run this in Supabase SQL Editor to allow your app to read/write data
-- Go to: supabase.com → your project → SQL Editor → New query → Paste → Run

-- Enable RLS (already enabled by default, but ensures it)
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE engagement_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminder_log ENABLE ROW LEVEL SECURITY;

-- Create permissive policies so the backend can do everything
CREATE POLICY "Allow all on students" ON students FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on courses" ON courses FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on enrollments" ON enrollments FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on engagement_log" ON engagement_log FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on reminder_log" ON reminder_log FOR ALL USING (true) WITH CHECK (true);
