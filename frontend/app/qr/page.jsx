import Link from "next/link";
import PlatformQrCode from "../../components/PlatformQrCode";

export const metadata = {
  title: "Share Global Learning Hub",
  description: "Download a QR code that opens the public learning hub page.",
};

export default function SharePage() {
  return (
    <main className="pageShell">
      <header className="siteHeader">
        <Link className="brand" href="/learn" aria-label="Global Learning Hub home">
          <span className="brandMark" aria-hidden="true">GL</span>
          <span>Global Learning Hub</span>
        </Link>
        <Link className="headerLink" href="/learn">Back to home</Link>
      </header>

      <section className="shareSection" aria-labelledby="share-title">
        <p className="eyebrow">A link to our site</p>
        <h1 id="share-title">Share the learning hub</h1>
        <p className="intro">
          Scan this code or download it to share the public entry page. You can
          also add the page link to a social profile; the QR does not connect or
          sign in to any social-media account.
        </p>
        <PlatformQrCode />
        <p className="smallPrint">
          The QR contains only this website address. It does not contain a
          password, learner information, or an access token.
        </p>
      </section>

      <footer className="siteFooter">
        <span>Global Learning Hub</span>
        <span>Learning access, one step at a time.</span>
      </footer>
    </main>
  );
}
