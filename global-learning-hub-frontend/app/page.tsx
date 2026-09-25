import { api } from "@/lib/api";

export default async function Dashboard() {
  let report = null;
  let error = "";
  try {
    report = await api.report();
  } catch {
    error = "The backend report is currently unavailable.";
  }

  return (
    <>
      <h1>Operations Dashboard</h1>
      <p>Monitor today's learning automation without exposing database credentials to the browser.</p>
      {error && <div className="notice error">{error}</div>}
      {report && (
        <section className="grid">
          <article><span>Courses today</span><b>{report.courses_today}</b></article>
          <article><span>Active enrollments</span><b>{report.total_enrolled}</b></article>
          <article><span>Reminders sent</span><b>{report.reminders.sent}</b></article>
          <article><span>Failed reminders</span><b>{report.reminders.failed}</b></article>
          <article><span>Active engagement</span><b>{report.engagement.active}</b></article>
          <article><span>Needs follow-up</span><b>{report.engagement.needs_followup}</b></article>
        </section>
      )}
    </>
  );
}
