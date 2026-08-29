/**
 * Notification triggers for the IOB Dindigul Merchant Services Portal.
 *
 * Replaces sendNewSubmissionNotification / sendStatusUpdateNotification from
 * the retired Google Apps Script backend. Firestore is now the only datastore,
 * so these fire off document writes rather than sheet appends.
 *
 * Configure before deploying:
 *   firebase functions:secrets:set SMTP_PASSWORD
 *   firebase deploy --only functions
 * and set SMTP_HOST / SMTP_PORT / SMTP_USER / NOTIFY_TO below or via env.
 */

const { onDocumentCreated, onDocumentUpdated } = require("firebase-functions/v2/firestore");
const { defineSecret, defineString } = require("firebase-functions/params");
const logger = require("firebase-functions/logger");
const nodemailer = require("nodemailer");

const SMTP_PASSWORD = defineSecret("SMTP_PASSWORD");
const SMTP_HOST = defineString("SMTP_HOST", { default: "smtp.gmail.com" });
const SMTP_PORT = defineString("SMTP_PORT", { default: "465" });
const SMTP_USER = defineString("SMTP_USER", { default: "" });
const NOTIFY_TO = defineString("NOTIFY_TO", { default: "satishpandian@iob.bank.in" });

const PORTAL_URL = "https://pandianss.github.io/IOB-Dindigul-Portal/";
const ADMIN_URL = "https://pandianss.github.io/IOB-Dindigul-Portal/admin.html";

const REGION = "asia-south1";

function transport() {
  return nodemailer.createTransport({
    host: SMTP_HOST.value(),
    port: parseInt(SMTP_PORT.value(), 10),
    secure: parseInt(SMTP_PORT.value(), 10) === 465,
    auth: { user: SMTP_USER.value(), pass: SMTP_PASSWORD.value() },
  });
}

function esc(v) {
  return String(v == null ? "" : v).replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function shell(subtitle, rows, ctaLabel, ctaHref, footer) {
  const body = rows
    .filter(([, v]) => v !== "" && v != null)
    .map(([k, v]) =>
      `<tr><td style="padding:8px 0;color:#6b7a99;width:35%"><strong>${esc(k)}:</strong></td>` +
      `<td style="padding:8px 0">${esc(v)}</td></tr>`)
    .join("");

  return `<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;border:1px solid #d0daf0;border-radius:12px;overflow:hidden">
  <div style="background:linear-gradient(90deg,#0d2354,#1a3a7a);color:#fff;padding:18px 24px">
    <h2 style="margin:0;font-size:1.15rem">🏦 Indian Overseas Bank — Dindigul RO</h2>
    <p style="margin:4px 0 0;font-size:0.85rem;opacity:0.85">${esc(subtitle)}</p>
  </div>
  <div style="padding:24px;color:#1a2440;line-height:1.5">
    <table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:0.88rem">${body}</table>
    <div style="margin-top:24px;text-align:center">
      <a href="${ctaHref}" style="background:#1a3a7a;color:#fff;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:bold;display:inline-block;font-size:0.88rem">${esc(ctaLabel)}</a>
    </div>
  </div>
  <div style="background:#f0f4ff;padding:12px 24px;font-size:0.75rem;color:#6b7a99;text-align:center">${esc(footer)}</div>
</div>`;
}

async function send(subject, html) {
  const to = NOTIFY_TO.value();
  const user = SMTP_USER.value();
  if (!to || !user) {
    logger.warn("Email skipped: SMTP_USER or NOTIFY_TO is not configured.");
    return;
  }
  await transport().sendMail({ from: user, to, subject, html });
  logger.info("Notification sent", { subject, to });
}

const TYPE_LABEL = { qr: "QR Code", soundbox: "Soundbox", lead: "Product Lead" };

exports.onNewRequest = onDocumentCreated(
  { document: "leads/{docId}", region: REGION, secrets: [SMTP_PASSWORD] },
  async (event) => {
    const d = event.data && event.data.data();
    if (!d) return;

    const serviceType = TYPE_LABEL[d.type] || "Request";
    const merchant = d.MERCHANTNAME || d.MERCHANT_NAME || d.ACCOUNT_NAME || "Merchant";
    const sol = d.SOL_ID || "-";

    await send(
      `🚨 New Request: ${serviceType} - ${merchant} (SOL ${sol})`,
      shell(
        "New Merchant Application / Lead Submitted",
        [
          ["Request Type", serviceType],
          ["Merchant Name", merchant],
          ["Mobile Number", d.MOBILENO || d.MOBILE_NO || d.MOBILE_NUMBER || "-"],
          ["Branch SOL ID", sol],
          ["Submitted By Staff", `${d.STAFF_NAME || "-"} (${d.STAFF_ROLL || "-"})`],
          ["Submission Time", d.CREATED_AT || new Date().toISOString()],
        ],
        "Open Admin Dashboard ⚙️",
        ADMIN_URL,
        "IOB Dindigul Regional Office • Automated Notification"
      )
    );
  }
);

exports.onStatusChange = onDocumentUpdated(
  { document: "leads/{docId}", region: REGION, secrets: [SMTP_PASSWORD] },
  async (event) => {
    const before = event.data.before.data();
    const after = event.data.after.data();
    if (!before || !after || before.STATUS === after.STATUS) return;

    const merchant = after.MERCHANTNAME || after.MERCHANT_NAME || after.ACCOUNT_NAME || "Merchant";

    await send(
      `🔔 Status Update: ${merchant} ➔ ${after.STATUS}`,
      shell(
        "Application / Lead Status Updated",
        [
          ["Merchant Name", merchant],
          ["Previous Status", before.STATUS || "-"],
          ["New Status", after.STATUS],
          ["Admin / Vendor Remarks", after.VENDOR_REMARKS || "N/A"],
          ["Generated VPA", after.MERCHANTVPA || ""],
          ["Staff Roll / Name", `${after.STAFF_NAME || "-"} (${after.STAFF_ROLL || "-"})`],
          ["Updated Time", after.UPDATED_DATE || new Date().toISOString()],
        ],
        "View in Portal 🔍",
        PORTAL_URL,
        "IOB Dindigul Regional Office • Automated Status Notification"
      )
    );
  }
);
