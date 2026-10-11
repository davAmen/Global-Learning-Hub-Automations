"use client";

import { useEffect, useState } from "react";
import ReportCard from "@/components/ReportCard";

export const dynamic = "force-dynamic";

export default function Home() {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${apiUrl}/reports/today`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setReport)
      .catch((err) => {
        setError(err.message);
        setReport(null);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ padding: "2rem", textAlign: "center" }}>Loading...</p>;
  if (error) return <p style={{ padding: "2rem", textAlign: "center", color: "#dc2626" }}>Error loading report: {error}</p>;
  if (!report) return <p style={{ padding: "2rem", textAlign: "center", color: "#dc2626" }}>Could not load today's report.</p>;
  return <ReportCard report={report} />;
}