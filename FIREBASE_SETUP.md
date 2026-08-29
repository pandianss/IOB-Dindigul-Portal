# Firebase Setup — IOB Dindigul Merchant Services Portal

The portal ran on a Google Apps Script + Sheets backend. It now runs entirely on
Firebase. The Apps Script project is no longer called by any page and can be
detached; its source remains in git history at commit `e20e183` if needed.

Project: **digitaldindigul-f78f9**
Hosting: GitHub Pages (unchanged) — only the backend moved.

## What lives where now

| Concern | Before | Now |
|---|---|---|
| Requests (QR / Soundbox / Lead) | Sheets tabs | Firestore `leads` collection |
| Staff directory | localStorage only | Firestore `staff` collection |
| QR PDF attachments | Google Drive | Cloud Storage `qr-pdfs/{docId}/` |
| Download counters | Sheet column | `DOWNLOAD_COUNT` field, atomic increment |
| Auto-soundbox on QR onboarding | Apps Script | Client-side `createLinkedSoundbox()` |
| Email notifications | `MailApp` | Cloud Functions `onNewRequest` / `onStatusChange` |
| Historical data | Sheets | Migrated — 103 records (77 QR, 15 SB, 11 Lead) |

## One-time console steps

1. **Enable Blaze billing** on the project. Cloud Storage and Cloud Functions
   both require it; the Spark plan cannot run either.
2. **Provision the Storage bucket** (Console → Build → Storage → Get started).
   Until this exists, attaching a PDF in the admin dashboard will hang.
3. **Enable Anonymous sign-in** (Console → Authentication → Sign-in method).
   The security rules require a signed-in caller and the pages call
   `signInAnonymously()` on load.

## Deploying rules and functions

```bash
npm --prefix functions install
firebase functions:secrets:set SMTP_PASSWORD
firebase deploy --only firestore:rules,storage:rules,functions
```

Set the non-secret mail settings as function params (or edit the defaults in
`functions/index.js`): `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `NOTIFY_TO`.

## Outstanding security work

The rules in `firestore.rules` gate on anonymous Firebase Auth. That stops
casual access by anyone who reads the config out of the page source, but it does
not prove who the caller is — anyone can obtain an anonymous token. Two things
still need doing:

- **App Check** (reCAPTCHA Enterprise) so only the real site can reach the API.
- **Real staff accounts** in Firebase Auth, replacing the roll-number +
  localStorage password scheme. Once staff carry a custom claim, swap the
  `signedIn()` checks in `firestore.rules` for role checks, and gate the
  `staff` collection to admins only.

Note also that `ADMIN_PASSWORD` in `admin.html` is a plaintext constant shipped
to every visitor. It gates the dashboard UI, not the data — the rules above are
what actually protect the records.
