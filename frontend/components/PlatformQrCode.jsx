"use client";

import { useEffect, useState } from "react";
import { QRCodeCanvas } from "qrcode.react";

function getLocalAccessScope(hostname) {
  const normalizedHost = hostname.replace(/^\[|\]$/g, "").toLowerCase();
  if (
    normalizedHost === "localhost" ||
    normalizedHost === "::1" ||
    normalizedHost.startsWith("127.")
  ) {
    return "same-device";
  }

  if (normalizedHost.endsWith(".local")) {
    return "local-network";
  }

  const octets = normalizedHost.split(".").map(Number);
  if (octets.length !== 4 || octets.some((octet) => !Number.isInteger(octet) || octet < 0 || octet > 255)) {
    if (normalizedHost.includes(":") && /^(fc|fd|fe80):/i.test(normalizedHost)) {
      return "local-network";
    }
    return null;
  }

  const isPrivateAddress = (
    octets[0] === 10 ||
    (octets[0] === 192 && octets[1] === 168) ||
    (octets[0] === 172 && octets[1] >= 16 && octets[1] <= 31)
  );
  return isPrivateAddress ? "local-network" : null;
}

export default function PlatformQrCode() {
  const [entryUrl, setEntryUrl] = useState("");
  const [localAccessScope, setLocalAccessScope] = useState(null);

  useEffect(() => {
    setEntryUrl(new URL("/learn", window.location.origin).toString());
    setLocalAccessScope(getLocalAccessScope(window.location.hostname));
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
      {localAccessScope === "same-device" && (
        <p className="localWarning" role="note">
          This QR contains a loopback address. It opens only on this computer;
          scanning it with a phone points back to the phone itself. To test from
          another device, use this computer&apos;s reachable local-network
          address. Access from anywhere needs a stable public HTTPS address and
          a later deployment.
        </p>
      )}
      {localAccessScope === "local-network" && (
        <p className="localWarning" role="note">
          This QR contains a private or local-network address. It works only on
          devices that can reach this computer on that network. Access from
          anywhere needs a stable public HTTPS address and a later deployment.
        </p>
      )}
    </div>
  );
}
