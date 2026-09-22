export default function ReportCard({ report }: { report: any }) {
  return (
    <div style={{ border: "1px solid #ccc", padding: "1rem", maxWidth: 400 }}>
      <h2>Daily Report - {report.date}</h2>
      <p>Courses today: {report.courses_today}</p>
      <p>Total enrolled: {report.total_enrolled}</p>
      <h3>Engagement</h3>
      <ul>
        <li>Active: {report.engagement?.active}</li>
        <li>Low engagement: {report.engagement?.low_engagement}</li>
        <li>Needs follow-up: {report.engagement?.needs_followup}</li>
      </ul>
      <h3>Reminders</h3>
      <p>Sent: {report.reminders?.sent}</p>
      <p>Failed: {report.reminders?.failed}</p>
    </div>
  );
}
