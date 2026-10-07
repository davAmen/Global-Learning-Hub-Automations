"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { fetchProfile, logout } from "@/lib/api";

export const metadata = { title: "Global Learning Hub" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<{ name: string; email: string; role: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const initAuth = async () => {
      try {
        const profile = await fetchProfile();
        setUser(profile);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    initAuth();
  }, []);

  const handleLogout = async () => {
    await logout();
    setUser(null);
    router.push("/");
  };

  if (loading) {
    return (
      <html lang="en">
        <body style={{ margin: 0, fontFamily: "system-ui, sans-serif" }}>
          <div style={{ padding: "2rem", textAlign: "center" }}>Loading...</div>
        </body>
      </html>
    );
  }

  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif", minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <nav style={{ padding: "1rem", borderBottom: "1px solid #e0e0e0", background: "#fff", position: "sticky", top: 0, zIndex: 100 }}>
          <div style={{ maxWidth: "1200px", margin: "0 auto", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <Link href="/" style={{ fontWeight: 700, fontSize: "1.25rem", color: "#2563eb", textDecoration: "none" }}>
              Global Learning Hub
            </Link>
            <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
              <Link href="/courses" style={{ color: "#374151", textDecoration: "none", fontWeight: 500, padding: "0.5rem 1rem", borderRadius: "0.375rem", transition: "background 0.2s" }}>Courses</Link>
              {user ? (
                <>
                  <Link href="/dashboard" style={{ color: "#374151", textDecoration: "none", fontWeight: 500, padding: "0.5rem 1rem", borderRadius: "0.375rem" }}>Dashboard</Link>
                  <span style={{ color: "#6b7280", fontSize: "0.875rem" }}>{user.name} ({user.role})</span>
                  <button onClick={handleLogout} style={{ background: "none", border: "1px solid #d1d5db", color: "#374151", padding: "0.375rem 1rem", borderRadius: "0.375rem", cursor: "pointer", fontSize: "0.875rem" }}>Logout</button>
                </>
              ) : (
                <>
                  <Link href="/login" style={{ color: "#374151", textDecoration: "none", fontWeight: 500, padding: "0.5rem 1rem", borderRadius: "0.375rem" }}>Login</Link>
                  <Link href="/register" style={{ background: "#2563eb", color: "#fff", textDecoration: "none", fontWeight: 600, padding: "0.5rem 1.25rem", borderRadius: "0.375rem", transition: "background 0.2s" }}>Sign Up</Link>
                </>
              )}
            </div>
          </div>
        </nav>
        <main style={{ flex: 1, padding: "2rem", maxWidth: "1200px", margin: "0 auto", width: "100%", boxSizing: "border-box" }}>
          {children}
        </main>
        <footer style={{ padding: "2rem", borderTop: "1px solid #e5e7eb", background: "#f9fafb", textAlign: "center", color: "#6b7280", fontSize: "0.875rem" }}>
          Global Learning Hub &copy; 2026 &mdash; Skills. Growth. Certification.
        </footer>
      </body>
    </html>
  );
}