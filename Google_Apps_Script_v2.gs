/**
 * Google Apps Script v2.9 for IOB Merchant Services & Leads Portal
 * Includes automated email notifications and LockService for High-Concurrency Concurrency Safety.
 */

// CONFIGURATION: Recipient email address for all portal notifications
var ADMIN_NOTIFICATION_EMAIL = "satishpandian@iob.bank.in";

// Sheets that hold configuration blobs (staff directory, guardian maps, role matrix,
// campaigns). These are NEVER merged into the merchant/lead feed the dashboard renders.
var CONFIG_SHEET = "Portal_Config";

function doGet(e) {
  var params = (e && e.parameter) || {};

  // Config reads are tiny and separate from the heavy lead feed.
  if (params.config) {
    return jsonOut({ status: "success", key: params.config, value: readConfigBlob(params.config) });
  }

  // Only the admin/targets screens need biz + base; the dashboard does not.
  var wantHeavy = params.include === "all";
  var cacheKey = wantHeavy ? "portal_feed_all" : "portal_feed_core";

  var cached = cacheGetChunked(cacheKey);
  if (cached && params.fresh !== "1") {
    return ContentService.createTextOutput(cached).setMimeType(ContentService.MimeType.JSON);
  }

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var qrSheet = ss.getSheetByName("QR_Template");
  var sbSheet = ss.getSheetByName("Soundbox_Template");
  var leadSheet = ss.getSheetByName("Leads_Template");

  var response = {
    qr: qrSheet ? readSheetDataFast(qrSheet, getQRHeaders()) : [],
    sb: sbSheet ? readSheetDataFast(sbSheet, getSBHeaders()) : [],
    lead: leadSheet ? readSheetDataFast(leadSheet, getLeadHeaders()) : [],
    biz: [],
    base: []
  };

  if (wantHeavy) {
    var bizSheet = ss.getSheetByName("Daily_Reporting");
    var baseSheet = ss.getSheetByName("Base_Targets");
    response.biz = bizSheet ? readSheetDataFast(bizSheet, getBizHeaders()) : [];
    response.base = baseSheet ? readSheetDataFast(baseSheet, getBaseHeaders()) : [];
  }

  var payload = JSON.stringify(response);
  cachePutChunked(cacheKey, payload, 45);
  return ContentService.createTextOutput(payload).setMimeType(ContentService.MimeType.JSON);
}

function jsonOut(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

// ── Chunked script cache (CacheService caps a single value at 100KB) ──
function cachePutChunked(key, value, seconds) {
  try {
    var cache = CacheService.getScriptCache();
    var size = 90000;
    var parts = Math.ceil(value.length / size);
    if (parts > 20) return; // too large to cache safely; serve live
    var map = {};
    for (var i = 0; i < parts; i++) {
      map[key + "_" + i] = value.substring(i * size, (i + 1) * size);
    }
    map[key + "_count"] = String(parts);
    cache.putAll(map, seconds);
  } catch (err) {}
}

function cacheGetChunked(key) {
  try {
    var cache = CacheService.getScriptCache();
    var countStr = cache.get(key + "_count");
    if (!countStr) return null;
    var parts = parseInt(countStr, 10);
    var keys = [];
    for (var i = 0; i < parts; i++) keys.push(key + "_" + i);
    var map = cache.getAll(keys);
    var out = "";
    for (var j = 0; j < parts; j++) {
      var piece = map[key + "_" + j];
      if (piece === null || piece === undefined) return null; // partial eviction
      out += piece;
    }
    return out;
  } catch (err) {
    return null;
  }
}

function invalidateFeedCache() {
  try {
    var cache = CacheService.getScriptCache();
    var keys = [];
    ["portal_feed_core", "portal_feed_all"].forEach(function(k) {
      keys.push(k + "_count");
      for (var i = 0; i < 20; i++) keys.push(k + "_" + i);
    });
    cache.removeAll(keys);
  } catch (err) {}
}

// ── Config blobs (staff directory, guardian maps, role matrix, campaigns) ──
function writeConfigBlob(ss, key, valueObj) {
  var sheet = getOrCreateSheet(ss, CONFIG_SHEET, ["CONFIG_KEY", "CONFIG_JSON", "UPDATED_DATE"]);
  var nowStr = Utilities.formatDate(new Date(), "Asia/Kolkata", "yyyy-MM-dd HH:mm:ss");
  var json = JSON.stringify(valueObj || {});
  var lastRow = sheet.getLastRow();
  if (lastRow > 1) {
    var keys = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
    for (var i = 0; i < keys.length; i++) {
      if (String(keys[i][0]) === key) {
        sheet.getRange(i + 2, 2, 1, 2).setValues([[json, nowStr]]);
        return;
      }
    }
  }
  sheet.appendRow([key, json, nowStr]);
}

function readConfigBlob(key) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG_SHEET);
  if (!sheet || sheet.getLastRow() < 2) return null;
  var rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, 2).getValues();
  for (var i = 0; i < rows.length; i++) {
    if (String(rows[i][0]) === key) {
      try { return JSON.parse(rows[i][1]); } catch (e) { return null; }
    }
  }
  return null;
}

function doPost(e) {
  // LOCK SERVICE: Wait up to 10 seconds to process concurrent simultaneous submissions safely
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000);
  } catch(e) {
    return ContentService.createTextOutput(JSON.stringify({ status: "error", message: "Server busy, please retry in a moment" }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  try {
    var contents = e.postData.contents;
    var data = JSON.parse(contents);
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    
    // ACTION: UPDATE STATUS (Used by Admin Dashboard)
    if (data.action === "updateStatus") {
      var sheet = ss.getSheetByName(data.sheetName);
      if (!sheet) throw new Error("Sheet not found: " + data.sheetName);
      
      var rowIndex = parseInt(data.rowIndex);
      var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
      
      var statusCol = headers.indexOf("STATUS") + 1;
      var dateCol = headers.indexOf("COMPLETED_DATE") + 1;
      if (dateCol === 0) dateCol = headers.indexOf("UPDATED_DATE") + 1;
      
      var vpaCol = headers.indexOf("MERCHANTVPA") + 1;
      var pdfCol = headers.indexOf("QR_PDF_URL") + 1;
      var remarksCol = headers.indexOf("VENDOR_REMARKS") + 1;
      
      var merchantCol = headers.indexOf("MERCHANTNAME") + 1;
      if (merchantCol === 0) merchantCol = headers.indexOf("MERCHANT_NAME") + 1;
      if (merchantCol === 0) merchantCol = headers.indexOf("ACCOUNT_NAME") + 1;
      
      var mobileCol = headers.indexOf("MOBILENO") + 1;
      if (mobileCol === 0) mobileCol = headers.indexOf("MOBILE_NO") + 1;
      if (mobileCol === 0) mobileCol = headers.indexOf("MOBILE_NUMBER") + 1;
      
      var staffRollCol = headers.indexOf("STAFF_ROLL") + 1;
      var staffNameCol = headers.indexOf("STAFF_NAME") + 1;
      
      var merchantName = merchantCol > 0 ? sheet.getRange(rowIndex, merchantCol).getValue() : "Merchant";
      var staffRoll = staffRollCol > 0 ? sheet.getRange(rowIndex, staffRollCol).getValue() : "";
      var staffName = staffNameCol > 0 ? sheet.getRange(rowIndex, staffNameCol).getValue() : "";
      
      var nowStr = Utilities.formatDate(new Date(), "Asia/Kolkata", "yyyy-MM-dd HH:mm:ss");
      
      if (statusCol > 0) sheet.getRange(rowIndex, statusCol).setValue(data.status);
      if (dateCol > 0) sheet.getRange(rowIndex, dateCol).setValue(nowStr);
      if (vpaCol > 0 && data.vpa) sheet.getRange(rowIndex, vpaCol).setValue(data.vpa);
      if (remarksCol > 0 && data.remarks) sheet.getRange(rowIndex, remarksCol).setValue(data.remarks);
      
      if (data.pdfBase64 && pdfCol > 0) {
        var pdfUrl = uploadPdfToDrive(data.pdfBase64, data.pdfName || "Document.pdf");
        sheet.getRange(rowIndex, pdfCol).setValue(pdfUrl);
      }
      
      // AUTOMATIC SOUNDBOX GENERATION
      if (data.sheetName === "QR_Template" && (data.status === "Completed" || data.status === "Merchant Onboarded") && data.soundboxRequired === "Yes") {
        createAutoSoundboxEntry(ss, sheet, rowIndex, data.vpa, data.solId, data.soundboxLang);
      }
      
      // EMAIL NOTIFICATION FOR STATUS UPDATE
      sendStatusUpdateNotification({
        sheetName: data.sheetName,
        merchantName: merchantName,
        status: data.status,
        remarks: data.remarks || "N/A",
        vpa: data.vpa || "",
        staffRoll: staffRoll,
        staffName: staffName,
        updatedDate: nowStr
      });
      
      invalidateFeedCache();
      return ContentService.createTextOutput(JSON.stringify({ status: "success", message: "Status updated successfully" }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    // ACTION: INCREMENT ATTACHMENT DOWNLOAD COUNTER
    if (data.action === "incrementDownload") {
      var sheet = ss.getSheetByName(data.sheetName);
      if (!sheet) throw new Error("Sheet not found: " + data.sheetName);
      
      var rowIndex = parseInt(data.rowIndex);
      var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
      
      var dlCol = headers.indexOf("DOWNLOAD_COUNT") + 1;
      if (dlCol === 0) {
        dlCol = headers.length + 1;
        sheet.getRange(1, dlCol).setValue("DOWNLOAD_COUNT");
      }
      
      var currentCount = parseInt(sheet.getRange(rowIndex, dlCol).getValue() || 0);
      var newCount = currentCount + 1;
      sheet.getRange(rowIndex, dlCol).setValue(newCount);
      
      return ContentService.createTextOutput(JSON.stringify({ status: "success", count: newCount }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    // ACTION: STAFF DIRECTORY & MAPPING CONFIG (Admin)
    // These are configuration blobs, NOT merchant leads. They go to Portal_Config so
    // staff rows can never surface in the dashboard's status table.
    if (data.action === "saveStaffMember" || data.action === "deleteStaffMember") {
      writeConfigBlob(ss, "staff_directory", data.fullDirectory || {});
      return jsonOut({ status: "success", message: "Staff directory saved", count: Object.keys(data.fullDirectory || {}).length });
    }

    if (data.action === "saveGuardianMap" || data.action === "saveGuardianMapMaster" || data.action === "saveGuardianBranchMap") {
      writeConfigBlob(ss, "guardian_map", data.map || data.guardianMap || data.fullMap || data);
      return jsonOut({ status: "success", message: "Guardian mapping saved" });
    }

    if (data.action === "saveRoleParamMapping") {
      writeConfigBlob(ss, "role_param_matrix", data.mapping || data.roleParamMapping || data.map || data);
      return jsonOut({ status: "success", message: "Role parameter matrix saved" });
    }

    if (data.action === "saveCampaigns") {
      writeConfigBlob(ss, "campaigns", data.campaigns || []);
      return jsonOut({ status: "success", message: "Campaigns saved" });
    }

    // ACTION: UPLOAD BASE TARGETS & YESTERDAY FIGURES (Admin Batch Upload)
    if (data.action === "uploadBaseTargets") {
      var baseSheet = getOrCreateSheet(ss, "Base_Targets", getBaseHeaders());
      var rows = data.rows || [];
      for (var b = 0; b < rows.length; b++) {
        appendDataRow(baseSheet, rows[b], getBaseHeaders());
      }
      return ContentService.createTextOutput(JSON.stringify({ status: "success", message: "Base targets uploaded successfully", count: rows.length }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    // Any request carrying an "action" is an admin/config call. If we reach here the
    // action is unrecognised — reject it explicitly rather than letting it fall through
    // into the submission branch below and be appended as a lead row.
    if (data.action) {
      throw new Error("Unknown action: " + data.action);
    }

    // ACTION: NEW SUBMISSION (QR, Soundbox, Lead, or Business)
    var nowStr =Utilities.formatDate(new Date(), "Asia/Kolkata", "yyyy-MM-dd HH:mm:ss");

    if (data.type === "qr") {
      var qrSheet = getOrCreateSheet(ss, "QR_Template", getQRHeaders());
      if (!data.qr.CREATED_DATE) data.qr.CREATED_DATE = nowStr;
      appendDataRow(qrSheet, data.qr, getQRHeaders());
      sendNewSubmissionNotification("Payment QR Code Application", data.qr);
    } else if (data.type === "soundbox") {
      var sbSheet = getOrCreateSheet(ss, "Soundbox_Template", getSBHeaders());
      if (!data.sb.CREATED_DATE) data.sb.CREATED_DATE = nowStr;
      appendDataRow(sbSheet, data.sb, getSBHeaders());
      sendNewSubmissionNotification("Soundbox Application", data.sb);
    } else if (data.type === "lead") {
      var leadSheet = getOrCreateSheet(ss, "Leads_Template", getLeadHeaders());
      if (!data.lead.CREATED_DATE) data.lead.CREATED_DATE = nowStr;
      if (!data.lead.UPDATED_DATE) data.lead.UPDATED_DATE = nowStr;
      appendDataRow(leadSheet, data.lead, getLeadHeaders());
      sendNewSubmissionNotification("Merchant Product Lead (" + (data.lead.PRODUCT || "POS") + ")", data.lead);
    } else if (data.type === "biz") {
      var bizSheet = getOrCreateSheet(ss, "Daily_Reporting", getBizHeaders());
      if (!data.biz.CREATED_DATE) data.biz.CREATED_DATE = nowStr;
      appendDataRow(bizSheet, data.biz, getBizHeaders());
      sendNewSubmissionNotification("General Business Daily Report (" + (data.biz.BRANCH_NAME || data.biz.SOL_ID) + ")", data.biz);
    } else {
      throw new Error("Invalid submission type");
    }
    
    invalidateFeedCache();
    return ContentService.createTextOutput(JSON.stringify({ status: "success", message: "Data submitted successfully" }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch(err) {
    return ContentService.createTextOutput(JSON.stringify({ status: "error", message: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}

function getQRHeaders() {
  return [
    "MERCHANTNAME", "MERCHANTVPA", "ACCOUNTNO", "IFSC", "MOBILENO", "MCCCODE",
    "ACTIVE", "ONBORDINGTYPE", "GSTNO", "EMAILID", "MERCHANTTYPE", "LATITUDE",
    "LONGITUDE", "ADDRESS1", "ADDRESS2", "POSTOFFICENAME", "PINCODE", "STATE",
    "DISTRICT", "SUBDISTRICT", "SOUNDBOX_REQUIRED", "SOL_ID", "SOUNDBOX_LANG",
    "STAFF_ROLL", "STAFF_NAME", "STATUS", "CREATED_DATE", "COMPLETED_DATE", "QR_PDF_URL", "DOWNLOAD_COUNT"
  ];
}

function getSBHeaders() {
  return [
    "SOL_ID", "BRANCH_NAME", "REGION", "VPA", "ACCOUNT_NAME", "ADDRESS",
    "PIN_CODE", "CITY", "STATE", "MCC", "MOBILE_NUMBER", "LANGUAGE",
    "STAFF_ROLL", "STAFF_NAME", "STATUS", "CREATED_DATE", "COMPLETED_DATE", "QR_PDF_URL", "DOWNLOAD_COUNT"
  ];
}

function getLeadHeaders() {
  return [
    "PRODUCT", "SOL_ID", "BRANCH_NAME", "ACCOUNT_NO", "MERCHANT_NAME",
    "MOBILE_NO", "NO_OF_DEVICES", "CONTACT_NAME", "CONTACT_MOBILE",
    "STAFF_ROLL", "STAFF_NAME", "STATUS", "CREATED_DATE", "UPDATED_DATE", "VENDOR_REMARKS"
  ];
}

function getBizHeaders() {
  return [
    "SOL_ID", "BRANCH_NAME", "REPORT_DATE", "STAFF_ROLL", "STAFF_NAME", "ROLE",
    "SB_GROWTH", "CD_GROWTH", "TD_GROWTH", "ACCTS_OPENED", "ACCTS_DIAMOND", "ACCTS_PLATINUM",
    "ACCTS_ULTRA_HNI", "ACCTS_PREMIUM", "ACCTS_GOVT", "ACCTS_TEMPLE", "ACCTS_CONTRACTORS",
    "LOW_BAL_FUNDED", "CREDIT_CARDS", "IOB_CONNECT", "NET_BANKING", "CASA_WINBACK",
    "NPS", "SSY", "PPF", "JL_FRESH", "JL_RENEWAL", "INOPERATIVE_COUNT", "INOPERATIVE_AMT",
    "INACTIVE_COUNT", "INACTIVE_AMT", "DEAF_COUNT", "DEAF_AMT", "REKYC_COUNT",
    "NOMINATION_COUNT", "DQI_SCORE", "POWERPLAY_INTENT", "CREATED_DATE"
  ];
}

function getBaseHeaders() {
  return [
    "SOL_ID", "BRANCH_NAME", "YEST_BAL_SB", "YEST_BAL_CD", "YEST_BAL_TD",
    "BAL_31MAR_SB", "BAL_31MAR_CD", "BAL_31MAR_TD", "UPTOYEST_ACCTS_SB", "UPTOYEST_ACCTS_CD",
    "BASE_INOPERATIVE_ACCTS", "BASE_INOPERATIVE_AMT", "BASE_INACTIVE_ACCTS", "BASE_INACTIVE_AMT",
    "BASE_DEAF_ACCTS", "BASE_DEAF_AMT"
  ];
}

function getOrCreateSheet(ss, name, headers) {
  var sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight("bold").setBackground("#1a3a7a").setFontColor("#ffffff");
    sheet.setFrozenRows(1);
  } else {
    if (sheet.getLastRow() >= 1) {
      var firstCell = sheet.getRange(1, 1).getValue().toString();
      if (firstCell !== headers[0]) {
        sheet.insertRowBefore(1);
        sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
        sheet.getRange(1, 1, 1, headers.length).setFontWeight("bold").setBackground("#1a3a7a").setFontColor("#ffffff");
        sheet.setFrozenRows(1);
      }
    } else {
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
      sheet.getRange(1, 1, 1, headers.length).setFontWeight("bold").setBackground("#1a3a7a").setFontColor("#ffffff");
      sheet.setFrozenRows(1);
    }
  }
  return sheet;
}

function readSheetDataFast(sheet, fallbackHeaders) {
  var lastRow = sheet.getLastRow();
  if (lastRow <= 1) return [];
  
  var allData = sheet.getDataRange().getValues();
  if (allData.length <= 1) return [];
  
  var headers = allData[0];
  var result = [];
  for (var i = 1; i < allData.length; i++) {
    var obj = { rowIndex: i + 1 };
    for (var j = 0; j < headers.length; j++) {
      var hKey = headers[j] ? headers[j].toString().trim() : fallbackHeaders[j];
      obj[hKey] = allData[i][j] !== undefined ? allData[i][j] : "";
    }
    result.push(obj);
  }
  return result;
}

function appendDataRow(sheet, dataObj, headers) {
  var row = [];
  for (var i = 0; i < headers.length; i++) {
    var key = headers[i];
    if (key === "STATUS") {
      row.push(dataObj.STATUS || "Pending");
    } else if (key === "CREATED_DATE") {
      row.push(dataObj.CREATED_DATE || Utilities.formatDate(new Date(), "Asia/Kolkata", "yyyy-MM-dd HH:mm:ss"));
    } else if (key === "COMPLETED_DATE" || key === "UPDATED_DATE") {
      row.push(dataObj[key] || "");
    } else {
      row.push(dataObj[key] !== undefined ? dataObj[key] : "");
    }
  }
  sheet.appendRow(row);
}

function uploadPdfToDrive(base64Data, filename) {
  var folderName = "IOB_Merchant_PDFs";
  var folders = DriveApp.getFoldersByName(folderName);
  var folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);
  
  var decoded = Utilities.base64Decode(base64Data);
  var blob = Utilities.newBlob(decoded, "application/pdf", filename);
  var file = folder.createFile(blob);
  file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  
  return file.getUrl();
}

function createAutoSoundboxEntry(ss, qrSheet, rowIndex, generatedVpa, solId, soundboxLang) {
  var sbSheet = getOrCreateSheet(ss, "Soundbox_Template", getSBHeaders());
  var headers = qrSheet.getRange(1, 1, 1, qrSheet.getLastColumn()).getValues()[0];
  var rowData = qrSheet.getRange(rowIndex, 1, 1, qrSheet.getLastColumn()).getValues()[0];
  
  function getVal(hName) {
    var idx = headers.indexOf(hName);
    return idx >= 0 ? rowData[idx] : "";
  }
  
  var nowStr = Utilities.formatDate(new Date(), "Asia/Kolkata", "yyyy-MM-dd HH:mm:ss");

  var sbObj = {
    SOL_ID: solId || getVal("SOL_ID") || "0174",
    BRANCH_NAME: "Branch " + (solId || getVal("SOL_ID") || "0174"),
    REGION: "Dindigul",
    VPA: generatedVpa || getVal("MERCHANTVPA") || "",
    ACCOUNT_NAME: getVal("MERCHANTNAME"),
    ADDRESS: getVal("ADDRESS1") + ", " + getVal("POSTOFFICENAME") + ", " + getVal("DISTRICT"),
    PIN_CODE: getVal("PINCODE"),
    CITY: getVal("DISTRICT"),
    STATE: getVal("STATE") || "Tamil Nadu",
    MCC: getVal("MCCCODE"),
    MOBILE_NUMBER: getVal("MOBILENO"),
    LANGUAGE: soundboxLang || getVal("SOUNDBOX_LANG") || "ta",
    STAFF_ROLL: getVal("STAFF_ROLL"),
    STAFF_NAME: getVal("STAFF_NAME"),
    STATUS: "Pending",
    CREATED_DATE: nowStr,
    COMPLETED_DATE: "",
    QR_PDF_URL: ""
  };
  
  appendDataRow(sbSheet, sbObj, getSBHeaders());
}

// ─────────────────────────────────────────────
// AUTOMATED EMAIL NOTIFICATIONS MODULE
// ─────────────────────────────────────────────
function sendNewSubmissionNotification(serviceType, data) {
  try {
    var recipient = ADMIN_NOTIFICATION_EMAIL || Session.getActiveUser().getEmail() || EffectiveUser.getEmail();
    if (!recipient) return;
    
    var merchantName = data.MERCHANTNAME || data.MERCHANT_NAME || data.ACCOUNT_NAME || "Merchant";
    var mobile = data.MOBILENO || data.MOBILE_NO || data.MOBILE_NUMBER || "-";
    var solId = data.SOL_ID || "-";
    var staffRoll = data.STAFF_ROLL || "-";
    var staffName = data.STAFF_NAME || "-";
    var createdDate = data.CREATED_DATE || Utilities.formatDate(new Date(), "Asia/Kolkata", "yyyy-MM-dd HH:mm:ss");

    var subject = "🚨 New Request: " + serviceType + " - " + merchantName + " (SOL " + solId + ")";
    
    var htmlBody = "" +
      "<div style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto;border:1px solid #d0daf0;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.08)'>" +
        "<div style='background:linear-gradient(90deg,#0d2354,#1a3a7a);color:#fff;padding:18px 24px'>" +
          "<h2 style='margin:0;font-size:1.15rem'>🏦 Indian Overseas Bank — Dindigul RO</h2>" +
          "<p style='margin:4px 0 0;font-size:0.85rem;opacity:0.85'>New Merchant Application / Lead Submitted</p>" +
        "</div>" +
        "<div style='padding:24px;color:#1a2440;line-height:1.5'>" +
          "<p style='font-size:0.95rem;margin-top:0'>A new request has been submitted by branch staff:</p>" +
          "<table style='width:100%;border-collapse:collapse;margin:16px 0;font-size:0.88rem'>" +
            "<tr><td style='padding:8px 0;color:#6b7a99;width:35%'><strong>Request Type:</strong></td><td style='padding:8px 0;color:#1a3a7a;font-weight:bold'>" + serviceType + "</td></tr>" +
            "<tr><td style='padding:8px 0;color:#6b7a99'><strong>Merchant Name:</strong></td><td style='padding:8px 0'>" + merchantName + "</td></tr>" +
            "<tr><td style='padding:8px 0;color:#6b7a99'><strong>Mobile Number:</strong></td><td style='padding:8px 0'>" + mobile + "</td></tr>" +
            "<tr><td style='padding:8px 0;color:#6b7a99'><strong>Branch SOL ID:</strong></td><td style='padding:8px 0'>" + solId + "</td></tr>" +
            "<tr><td style='padding:8px 0;color:#6b7a99'><strong>Submitted By Staff:</strong></td><td style='padding:8px 0'>" + staffName + " (" + staffRoll + ")</td></tr>" +
            "<tr><td style='padding:8px 0;color:#6b7a99'><strong>Submission Time:</strong></td><td style='padding:8px 0'>" + createdDate + "</td></tr>" +
          "</table>" +
          "<div style='margin-top:24px;text-align:center'>" +
            "<a href='https://pandianss.github.io/IOB-Merchant-Request/admin.html' style='background:#1a3a7a;color:#fff;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:bold;display:inline-block;font-size:0.88rem'>Open Admin Dashboard ⚙️</a>" +
          "</div>" +
        "</div>" +
        "<div style='background:#f0f4ff;padding:12px 24px;font-size:0.75rem;color:#6b7a99;text-align:center'>" +
          "IOB Dindigul Regional Office • Automated Notification" +
        "</div>" +
      "</div>";

    MailApp.sendEmail({
      to: recipient,
      subject: subject,
      htmlBody: htmlBody
    });
  } catch(e) {
    Logger.log("Email error: " + e.toString());
  }
}

function sendStatusUpdateNotification(data) {
  try {
    var recipient = ADMIN_NOTIFICATION_EMAIL || Session.getActiveUser().getEmail() || EffectiveUser.getEmail();
    if (!recipient) return;

    var subject = "🔔 Status Update: " + data.merchantName + " ➔ " + data.status;
    
    var htmlBody = "" +
      "<div style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto;border:1px solid #d0daf0;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.08)'>" +
        "<div style='background:linear-gradient(90deg,#0d2354,#1a3a7a);color:#fff;padding:18px 24px'>" +
          "<h2 style='margin:0;font-size:1.15rem'>🏦 Indian Overseas Bank — Dindigul RO</h2>" +
          "<p style='margin:4px 0 0;font-size:0.85rem;opacity:0.85'>Application / Lead Status Updated</p>" +
        "</div>" +
        "<div style='padding:24px;color:#1a2440;line-height:1.5'>" +
          "<p style='font-size:0.95rem;margin-top:0'>The status of a merchant request has been updated by Admin:</p>" +
          "<table style='width:100%;border-collapse:collapse;margin:16px 0;font-size:0.88rem'>" +
            "<tr><td style='padding:8px 0;color:#6b7a99;width:35%'><strong>Merchant Name:</strong></td><td style='padding:8px 0;font-weight:bold'>" + data.merchantName + "</td></tr>" +
            "<tr><td style='padding:8px 0;color:#6b7a99'><strong>New Status:</strong></td><td style='padding:8px 0;color:#166534;font-weight:bold'>" + data.status + "</td></tr>" +
            "<tr><td style='padding:8px 0;color:#6b7a99'><strong>Admin / Vendor Remarks:</strong></td><td style='padding:8px 0;font-style:italic'>" + data.remarks + "</td></tr>" +
            (data.vpa ? "<tr><td style='padding:8px 0;color:#6b7a99'><strong>Generated VPA:</strong></td><td style='padding:8px 0;color:#1a3a7a;font-weight:bold'>" + data.vpa + "</td></tr>" : "") +
            "<tr><td style='padding:8px 0;color:#6b7a99'><strong>Staff Roll / Name:</strong></td><td style='padding:8px 0'>" + data.staffName + " (" + data.staffRoll + ")</td></tr>" +
            "<tr><td style='padding:8px 0;color:#6b7a99'><strong>Updated Time:</strong></td><td style='padding:8px 0'>" + data.updatedDate + "</td></tr>" +
          "</table>" +
          "<div style='margin-top:24px;text-align:center'>" +
            "<a href='https://pandianss.github.io/IOB-Merchant-Request/' style='background:#1a3a7a;color:#fff;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:bold;display:inline-block;font-size:0.88rem'>View in Portal 🔍</a>" +
          "</div>" +
        "</div>" +
        "<div style='background:#f0f4ff;padding:12px 24px;font-size:0.75rem;color:#6b7a99;text-align:center'>" +
          "IOB Dindigul Regional Office • Automated Status Notification" +
        "</div>" +
      "</div>";

    MailApp.sendEmail({
      to: recipient,
      subject: subject,
      htmlBody: htmlBody
    });
  } catch(e) {
    Logger.log("Email update error: " + e.toString());
  }
}
