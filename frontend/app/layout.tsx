import { Metadata } from "next";
import { AuthNav } from "@/components/AuthNav";

export const metadata: Metadata = { title: "Global Learning Hub" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif", minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <AuthNav />
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