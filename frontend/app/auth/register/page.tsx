"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { register } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setLoading(true);

    try {
      await register({ name, email, password, phone: phone || undefined });
      router.push("/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem", background: "#f9fafb" }}>
      <div style={{ width: "100%", maxWidth: "420px", background: "#fff", borderRadius: "1rem", padding: "2.5rem", boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1)" }}>
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <Link href="/" style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", fontSize: "1.5rem", fontWeight: 800, color: "#2563eb", textDecoration: "none", marginBottom: "1.5rem" }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
            <span>Global Learning Hub</span>
          </Link>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#111827", marginBottom: "0.5rem" }}>Create your account</h1>
          <p style={{ color: "#6b7280" }}>Start your learning journey today</p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {error && (
            <div style={{ background: "#fef2f2", border: "1px solid #fecaca", color: "#dc2626", padding: "0.875rem 1rem", borderRadius: "0.5rem", fontSize: "0.875rem" }}>
              {error}
            </div>
)}

          <div>
            <label htmlFor="name" style={{ display: "block", fontSize: "0.875rem", fontWeight: 500, color: "#374151", marginBottom: "0.5rem" }}>Full Name</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              autoComplete="name"
              style={{ width: "100%", padding: "0.75rem 1rem", border: "1px solid #d1d5db", borderRadius: "0.5rem", fontSize: "1rem", transition: "border 0.2s, box-shadow 0.2s", boxSizing: "border-box" }}
              placeholder="John Doe"
            />
          </div>

          <div>
            <label htmlFor="email" style={{ display: "block", fontSize: "0.875rem", fontWeight: 500, color: "#374151", marginBottom: "0.5rem" }}>Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              style={{ width: "100%", padding: "0.75rem 1rem", border: "1px solid #d1d5db", borderRadius: "0.5rem", fontSize: "1rem", transition: "border 0.2s, box-shadow 0.2s", boxSizing: "border-box" }}
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label htmlFor="phone" style={{ display: "block", fontSize: "0.875rem", fontWeight: 500, color: "#374151", marginBottom: "0.5rem" }}>Phone (optional)</label>
            <input
              id="phone"
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              autoComplete="tel"
              style={{ width: "100%", padding: "0.75rem 1rem", border: "1px solid #d1d5db", borderRadius: "0.5rem", fontSize: "1rem", transition: "border 0.2s, box-shadow 0.2s", boxSizing: "border-box" }}
              placeholder="+233 54 801 4157"
            />
          </div>

          <div>
            <label htmlFor="password" style={{ display: "block", fontSize: "0.875rem", fontWeight: 500, color: "#374151", marginBottom: "0.5rem" }}>Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="new-password"
              minLength={8}
              style={{ width: "100%", padding: "0.75rem 1rem", border: "1px solid #d1d5db", borderRadius: "0.5rem", fontSize: "1rem", transition: "border 0.2s, box-shadow 0.2s", boxSizing: "border-box" }}
              placeholder="••••••••"
            />
            <p style={{ marginTop: "0.375rem", fontSize: "0.75rem", color: "#9ca3af" }}>At least 8 characters</p>
          </div>

          <div>
            <label htmlFor="confirmPassword" style={{ display: "block", fontSize: "0.875rem", fontWeight: 500, color: "#374151", marginBottom: "0.5rem" }}>Confirm Password</label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              autoComplete="new-password"
              style={{ width: "100%", padding: "0.75rem 1rem", border: "1px solid #d1d5db", borderRadius: "0.5rem", fontSize: "1rem", transition: "border 0.2s, box-shadow 0.2s", boxSizing: "border-box" }}
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{ width: "100%", padding: "0.875rem 1.5rem", background: "#2563eb", color: "#fff", border: "none", borderRadius: "0.5rem", fontSize: "1rem", fontWeight: 600, cursor: loading ? "not-allowed" : "pointer", transition: "background 0.2s" }}
          >
            {loading ? (
              <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", gap: "0.5rem" }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: "spin 1s linear infinite" }}>
                  <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
                  <path d="M12 2v4" />
                  <style jsx>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
                </svg>
                Creating account...
              </span>
            ) : (
              "Create Account"
            )}
          </button>
        </form>

        <div style={{ marginTop: "1.5rem", paddingTop: "1.5rem", borderTop: "1px solid #e5e7eb", textAlign: "center" }}>
          <p style={{ color: "#6b7280", margin: 0, fontSize: "0.875rem" }}>
            Already have an account?{" "}
            <Link href="/login" style={{ color: "#2563eb", fontWeight: 600, textDecoration: "none" }}>Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
