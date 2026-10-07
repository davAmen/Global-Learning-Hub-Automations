import "./globals.css";

export const metadata = {
  title: "Global Learning Hub",
  description: "A public starting point for the Global Learning Hub.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
