"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { fetchProfile } from "@/lib/api";

export default function ResendVerificationPage() {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const resendVerification = async () => {
    setError("");
    setMessage("");
    setSubmitting(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/auth/resend-verification`, {
        method: "POST",
        credentials: "include",
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to resend");
      setMessage(data.message || "Verification email sent");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resend");
    } finally {
      setSubmitting(false);
    }
  };

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const profile = await fetchProfile();
        if (profile.email_verified) {
          router.push("/dashboard");
        }
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, [router]);

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem", background: "#f9fafb" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ display: "inline-block", width: "2rem", height: "2rem", border: "3px solid #e5e7eb", borderTopColor: "#2563eb", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
          <style jsx>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
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
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#111827", marginBottom: "0.5rem" }}>Resend Verification</h1>
          <p style={{ color: "#6b7280" }}>Click below to send a new verification email</p>
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

        <button
          onClick={resendVerification}
          disabled={submitting}
          style={{ width: "100%", padding: "0.875rem 1.5rem", background: "#2563eb", color: "#fff", border: "none", borderRadius: "0.5rem", fontSize: "1rem", fontWeight: 600, cursor: submitting ? "not-allowed" : "pointer", transition: "background 0.2s" }}
        >
          {submitting ? "Sending..." : "Resend Verification Email"}
        </button>

        <div style={{ marginTop: "1.5rem", paddingTop: "1.5rem", borderTop: "1px solid #e5e7eb", textAlign: "center" }}>
          <p style={{ color: "#6b7280", margin: 0, fontSize: "0.875rem" }}>
            Already verified?{" "}
            <Link href="/login" style={{ color: "#2563eb", fontWeight: 600, textDecoration: "none" }}>Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}