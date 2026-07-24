/**
 * Google Apps Script v2.8 for IOB Merchant Services & Leads Portal
 * Includes automated email notifications for Submissions & Status Updates.
 */

// CONFIGURATION: Set default admin notification email recipient(s)
var ADMIN_NOTIFICATION_EMAIL = ""; // E.g., "admin@iob.in" or leave blank to send to script owner

function doGet(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  
  var qrSheet = ss.getSheetByName("QR_Template");
  var sbSheet = ss.getSheetByName("Soundbox_Template");
  var leadSheet = ss.getSheetByName("Leads_Template");
  
  var response = {
    qr: qrSheet ? readSheetDataFast(qrSheet, getQRHeaders()) : [],
    sb: sbSheet ? readSheetDataFast(sbSheet, getSBHeaders()) : [],
    lead: leadSheet ? readSheetDataFast(leadSheet, getLeadHeaders()) : []
  };
  
  return ContentService.createTextOutput(JSON.stringify(response))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
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
      
      return ContentService.createTextOutput(JSON.stringify({ status: "success", message: "Status updated successfully" }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    // ACTION: NEW SUBMISSION (QR, Soundbox, or Lead)
    var nowStr = Utilities.formatDate(new Date(), "Asia/Kolkata", "yyyy-MM-dd HH:mm:ss");

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
    } else {
      throw new Error("Invalid submission type");
    }
    
    return ContentService.createTextOutput(JSON.stringify({ status: "success", message: "Data submitted successfully" }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch(err) {
    return ContentService.createTextOutput(JSON.stringify({ status: "error", message: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function getQRHeaders() {
  return [
    "MERCHANTNAME", "MERCHANTVPA", "ACCOUNTNO", "IFSC", "MOBILENO", "MCCCODE",
    "ACTIVE", "ONBORDINGTYPE", "GSTNO", "EMAILID", "MERCHANTTYPE", "LATITUDE",
    "LONGITUDE", "ADDRESS1", "ADDRESS2", "POSTOFFICENAME", "PINCODE", "STATE",
    "DISTRICT", "SUBDISTRICT", "SOUNDBOX_REQUIRED", "SOL_ID", "SOUNDBOX_LANG",
    "STAFF_ROLL", "STAFF_NAME", "STATUS", "CREATED_DATE", "COMPLETED_DATE", "QR_PDF_URL"
  ];
}

function getSBHeaders() {
  return [
    "SOL_ID", "BRANCH_NAME", "REGION", "VPA", "ACCOUNT_NAME", "ADDRESS",
    "PIN_CODE", "CITY", "STATE", "MCC", "MOBILE_NUMBER", "LANGUAGE",
    "STAFF_ROLL", "STAFF_NAME", "STATUS", "CREATED_DATE", "COMPLETED_DATE", "QR_PDF_URL"
  ];
}

function getLeadHeaders() {
  return [
    "PRODUCT", "SOL_ID", "BRANCH_NAME", "ACCOUNT_NO", "MERCHANT_NAME",
    "MOBILE_NO", "NO_OF_DEVICES", "CONTACT_NAME", "CONTACT_MOBILE",
    "STAFF_ROLL", "STAFF_NAME", "STATUS", "CREATED_DATE", "UPDATED_DATE", "VENDOR_REMARKS"
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
          "<h2 style='margin:0;font-size:1.15rem'>🏦 Indian Overseas Bank</h2>" +
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
          "IOB Merchant Services Portal • Automated System Notification" +
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
          "<h2 style='margin:0;font-size:1.15rem'>🏦 Indian Overseas Bank</h2>" +
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
          "IOB Merchant Services Portal • Automated Status Notification" +
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
