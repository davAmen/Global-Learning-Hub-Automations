# Global Learning Hub entry preview

This small local web app provides the public entry page and a QR code that opens it. It does not yet provide learner accounts, courses, or classroom features.

## Run on Windows with PowerShell

From this `frontend` folder, run:

```powershell
npm install
npm run dev
```

Then open <http://localhost:3000>. Select **Get the share QR code** to see the QR or download it as a PNG.

The QR contains only the `/learn` page address for the site currently open. A `localhost` address works only on the same computer. A home or school Wi-Fi address usually works only for devices on that local network. A QR that works for people anywhere needs a stable public HTTPS address; this preview has not been deployed.

To make a production build locally, run:

```powershell
npm run build
```
