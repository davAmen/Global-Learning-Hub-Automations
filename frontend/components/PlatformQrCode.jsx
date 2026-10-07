"use client";

import { useEffect, useState } from "react";
import { QRCodeCanvas } from "qrcode.react";

function isLocalAddress(hostname) {
  const normalizedHost = hostname.replace(/^\[|\]$/g, "").toLowerCase();
  if (
    normalizedHost === "localhost" ||
    normalizedHost === "::1" ||
    normalizedHost.endsWith(".local")
  ) {
    return true;
  }

  const octets = normalizedHost.split(".").map(Number);
  if (octets.length !== 4 || octets.some((octet) => !Number.isInteger(octet) || octet < 0 || octet > 255)) {
    return false;
  }

  return (
    octets[0] === 10 ||
    octets[0] === 127 ||
    (octets[0] === 192 && octets[1] === 168) ||
    (octets[0] === 172 && octets[1] >= 16 && octets[1] <= 31)
  );
}

export default function PlatformQrCode() {
  const [entryUrl, setEntryUrl] = useState("");
  const [isLocal, setIsLocal] = useState(false);

  useEffect(() => {
    setEntryUrl(new URL("/learn", window.location.origin).toString());
    setIsLocal(isLocalAddress(window.location.hostname));
  }, []);

  function downloadQr() {
    const canvas = document.getElementById("platform-entry-qr");
    if (!(canvas instanceof HTMLCanvasElement)) {
      return;
    }

    const downloadLink = document.createElement("a");
    downloadLink.href = canvas.toDataURL("image/png");
    downloadLink.download = "global-learning-hub-qr.png";
    downloadLink.click();
  }

  if (!entryUrl) {
    return <p role="status">Preparing the QR code…</p>;
  }

  return (
    <div className="qrPanel">
      <div className="qrFrame">
        <QRCodeCanvas
          id="platform-entry-qr"
          value={entryUrl}
          size={400}
          level="M"
          includeMargin
          title="QR code linking to the Global Learning Hub public page"
        />
      </div>
      <p className="qrUrl">
        <a href={entryUrl}>{entryUrl}</a>
      </p>
      <button className="primaryButton" type="button" onClick={downloadQr}>
        Download QR image (PNG)
      </button>
      {isLocal && (
        <p className="localWarning" role="note">
          This is a local address. The QR will work only on this computer or on
          devices that can reach this local network. A reusable QR for people
          anywhere needs a stable public website address and a later deployment.
        </p>
      )}
    </div>
  );
}
