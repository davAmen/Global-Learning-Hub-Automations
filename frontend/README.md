# Global Learning Hub public entry

This frontend provides the public entry page and QR code. It does not yet provide learner accounts, courses, or classroom features. The production site is <https://globallearninghub.vercel.app>.

## Run on Windows with PowerShell

From this `frontend` folder, run:

```powershell
npm install
npm run dev
```

Then open <http://localhost:3000>. Select **Get the share QR code** to see the QR or download it as a PNG.

The QR contains only the `/learn` page address for the site currently open. A `localhost` address works only on the same computer. A home or school Wi-Fi address usually works only for devices on that local network. For a QR that works anywhere, use the production site at <https://globallearninghub.vercel.app/qr>.

To make a production build locally, run:

```powershell
npm run build
```
