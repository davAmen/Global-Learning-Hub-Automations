"use client";

import { useEffect, useState } from "react";
import ReportCard from "@/components/ReportCard";

export default function Home() {
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
  if (!report) return <p>Could not load today's report.</p>;
  return <ReportCard report={report} />;
}
