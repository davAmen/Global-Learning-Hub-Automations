"use client";

import { useState } from "react";

export default function RunJobButton() {
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/run-daily-job`, {
        method: "POST",
      });
      const data = await res.json();
      setResult(`Done. Sent ${data.reminders_sent} reminders.`);
    } catch {
      setResult("Failed to run job.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={handleClick} disabled={loading} style={{ padding: "0.5rem 1rem" }}>
        {loading ? "Running..." : "Run Today's Job"}
      </button>
      {result && <p>{result}</p>}
    </div>
  );
}
