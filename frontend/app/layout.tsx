export const metadata = { title: "Global Learning Hub" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav style={{ padding: "1rem", borderBottom: "1px solid #ccc" }}>
          <a href="/" style={{ marginRight: "1rem" }}>Home</a>
          <a href="/students" style={{ marginRight: "1rem" }}>Students</a>
          <a href="/courses" style={{ marginRight: "1rem" }}>Courses</a>
          <a href="/run">Run Job</a>
        </nav>
        <main style={{ padding: "2rem" }}>{children}</main>
      </body>
    </html>
  );
}
