"use client";

export default function VerifyEmailLoading() {
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