import Link from "next/link";

export default function LearnPage() {
  return (
    <main className="pageShell">
      <header className="siteHeader">
        <Link className="brand" href="/learn" aria-label="Global Learning Hub home">
          <span className="brandMark" aria-hidden="true">GL</span>
          <span>Global Learning Hub</span>
        </Link>
        <Link className="headerLink" href="/qr">Share this page</Link>
      </header>

      <section className="hero" aria-labelledby="welcome-title">
        <p className="eyebrow">A learning platform in progress</p>
        <h1 id="welcome-title">Your learning starts here.</h1>
        <p className="intro">
          This is the public entry page for Global Learning Hub. We are building
          a convenient place for learners and teachers to meet, learn, and share
          resources.
        </p>
        <p className="previewNote">
          This preview is only an entry page. Courses, accounts, and classroom
          features are not available here yet.
        </p>
        <Link className="primaryButton" href="/qr">Get the share QR code</Link>
      </section>

      <footer className="siteFooter">
        <span>Global Learning Hub</span>
        <span>Learning access, one step at a time.</span>
      </footer>
    </main>
  );
}
