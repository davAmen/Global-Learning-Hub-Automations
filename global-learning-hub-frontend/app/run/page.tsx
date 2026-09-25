"use client";

import { FormEvent, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function RunAutomation() {
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function run(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const response = await fetch(`${API_URL}/run-daily-job`, {
        method: "POST",
        headers: { "x-admin-key": key }
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Automation failed");
      setMessage(`Completed. ${body.reminders_sent} reminder(s) sent.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Automation failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <h1>Run Daily Automation</h1>
      <p>This action is administrator-protected. The key is sent to the backend and is not stored by this page.</p>
      <form onSubmit={run}>
        <label>Administrator key<input type="password" value={key} onChange={e => setKey(e.target.value)} required /></label>
        <button disabled={busy}>{busy ? "Running…" : "Run automation"}</button>
      </form>
      {message && <div className="notice">{message}</div>}
    </>
  );
}
