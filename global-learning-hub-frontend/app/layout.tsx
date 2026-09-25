import "./globals.css";
import Link from "next/link";

export const metadata = {
  title: "Global Learning Hub",
  description: "Learning automation operations dashboard"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header>
          <strong>Global Learning Hub</strong>
          <nav>
            <Link href="/">Dashboard</Link>
            <Link href="/run">Automation</Link>
          </nav>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
