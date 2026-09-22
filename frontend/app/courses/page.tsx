"use client";

import { useEffect, useState } from "react";

export default function CoursesPage() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/reports/today`)
      .then((r) => r.json())
      .then(setReport)
      .catch(() => setReport(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading...</p>;
  if (!report) return <p>Could not load course data.</p>;

  return (
    <div>
      <h1>Courses</h1>
      <p>Courses today: {report.courses_today}</p>
      <p>Total enrolled: {report.total_enrolled}</p>
    </div>
  );
}
