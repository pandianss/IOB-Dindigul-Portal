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

The dashboard password is now stored as a SHA-256 hash (`ADMIN_PASSWORD_SHA256`
in `admin.html`) rather than plaintext, so it is no longer readable in page
source. That raises the bar but is not a security boundary: the hash is still
shipped to every visitor and is brute-forceable offline, and the dashboard only
gates the UI — anyone can call Firestore directly. The rules above are what
actually protect the records. To change the password, replace the constant with
the SHA-256 of the new one.

## Deployment order

These are order-dependent. Doing them out of order takes the portal down:

1. **Enable Anonymous sign-in** (Authentication -> Sign-in method). Until this
   is on, `signInAnonymously()` fails with `auth/configuration-not-found`.
2. **Then** deploy `firestore.rules`. The rules require `request.auth != null`,
   so deploying them while step 1 is undone locks every user out.
3. Provision the Storage bucket, or attaching a PDF in the admin dashboard hangs.

## One-off data cleanup

`data-corrections.html` recomputes the mechanically certain corrections (IFSC
rebuilt from the record's own SOL, restored leading zeros on 15-digit accounts,
emails missing an `@` or a dot, soundbox VPAs on `@iob.in`), shows them as a
before/after table, and applies them on click. Originals are preserved on each
document under `DATA_CORRECTED_FROM`.

Items that need a person to resolve are listed in `DATA_WORKLIST.csv`.

### Status of the one-off cleanup

The 16 mechanically certain corrections were applied on 2026-09-15. Each
affected document carries `DATA_CORRECTED_FROM` with its original values, so
nothing was destroyed. Remaining after that pass: 1 IFSC, 2 emails and 3
soundbox VPAs that need a person, plus 2 duplicate pairs — all in
`DATA_WORKLIST.csv`.

### Applying further corrections

`data-corrections.html` cannot write while the deployed rules are in force:
`onlyWorkflowFields()` deliberately excludes `IFSC`, `EMAILID`, `ACCOUNT_NO`
and `VPA`, because those are exactly the fields that must not be tamperable by
an anonymous caller. To correct one of them you have two options:

- Edit the document directly in the Firebase console, which bypasses rules.
- Or open a short window: add the field names to the `hasOnly([...])` list in
  `firestore.rules`, `firebase deploy --only firestore:rules`, run the tool,
  then `git checkout -- firestore.rules` and deploy again. Verify the window is
  shut by attempting a protected-field write with a **genuinely different**
  value — writing the same value produces an empty diff and passes regardless,
  which makes for a misleading test.

Deleting a record always requires the console or a privileged Cloud Function:
`allow delete: if false` applies to every client, which is what stops a
drive-by wipe. The duplicate pairs in the worklist therefore have to be removed
from the console.
