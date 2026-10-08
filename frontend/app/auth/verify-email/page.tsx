"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { verifyEmail } from "@/lib/api";

export default function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setError("Invalid verification link");
      setLoading(false);
      return;
    }

    const doVerify = async () => {
      try {
        const data = await verifyEmail(token);
        setMessage(data.message || "Email verified successfully");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Verification failed");
      } finally {
        setLoading(false);
      }
    };

    doVerify();
  }, [searchParams]);

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem", background: "#f9fafb" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ display: "inline-block", width: "2rem", height: "2rem", border: "3px solid #e5e7eb", borderTopColor: "#2563eb", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
          <style jsx>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          <p style={{ marginTop: "1rem", color: "#6b7280" }}>Verifying your email...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem", background: "#f9fafb" }}>
      <div style={{ width: "100%", maxWidth: "420px", background: "#fff", borderRadius: "1rem", padding: "2.5rem", boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1)" }}>
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <Link href="/" style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", fontSize: "1.5rem", fontWeight: 800, color: "#2563eb", textDecoration: "none", marginBottom: "1.5rem" }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
            <span>Global Learning Hub</span>
          </Link>
          {message && <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#166534", marginBottom: "0.5rem" }}>Success!</h1>}
          {error && <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#dc2626", marginBottom: "0.5rem" }}>Verification Failed</h1>}
        </div>

        {message && (
          <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", color: "#166534", padding: "1rem", borderRadius: "0.5rem", marginBottom: "1.5rem" }}>
            {message}
          </div>
        )}
        {error && (
          <div style={{ background: "#fef2f2", border: "1px solid #fecaca", color: "#dc2626", padding: "1rem", borderRadius: "0.5rem", marginBottom: "1.5rem" }}>
            {error}
          </div>
        )}

        <div style={{ textAlign: "center" }}>
          <Link href="/login" style={{ display: "inline-block", padding: "0.75rem 1.5rem", background: "#2563eb", color: "#fff", borderRadius: "0.5rem", fontWeight: 600, textDecoration: "none" }}>
            Go to Login
          </Link>
        </div>
      </div>
    </div>
  );
}