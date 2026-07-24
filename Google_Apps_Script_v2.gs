/**
 * Google Apps Script v2.7 for IOB Merchant Services & Leads Portal
 * Includes explicit CREATED_DATE tracking for all QR, Soundbox, and Lead templates.
 */

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
      
      var nowStr = Utilities.formatDate(new Date(), "Asia/Kolkata", "yyyy-MM-dd HH:mm:ss");
      
      if (statusCol > 0) sheet.getRange(rowIndex, statusCol).setValue(data.status);
      if (dateCol > 0) sheet.getRange(rowIndex, dateCol).setValue(nowStr);
      if (vpaCol > 0 && data.vpa) sheet.getRange(rowIndex, vpaCol).setValue(data.vpa);
      if (remarksCol > 0 && data.remarks) sheet.getRange(rowIndex, remarksCol).setValue(data.remarks);
      
      if (data.pdfBase64 && pdfCol > 0) {
        var pdfUrl = uploadPdfToDrive(data.pdfBase64, data.pdfName || "Document.pdf");
        sheet.getRange(rowIndex, pdfCol).setValue(pdfUrl);
      }
      
      if (data.sheetName === "QR_Template" && (data.status === "Completed" || data.status === "Merchant Onboarded") && data.soundboxRequired === "Yes") {
        createAutoSoundboxEntry(ss, sheet, rowIndex, data.vpa, data.solId, data.soundboxLang);
      }
      
      return ContentService.createTextOutput(JSON.stringify({ status: "success", message: "Status updated successfully" }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    // ACTION: NEW SUBMISSION (QR, Soundbox, or Lead)
    var nowStr = Utilities.formatDate(new Date(), "Asia/Kolkata", "yyyy-MM-dd HH:mm:ss");

    if (data.type === "qr") {
      var qrSheet = getOrCreateSheet(ss, "QR_Template", getQRHeaders());
      if (!data.qr.CREATED_DATE) data.qr.CREATED_DATE = nowStr;
      appendDataRow(qrSheet, data.qr, getQRHeaders());
    } else if (data.type === "soundbox") {
      var sbSheet = getOrCreateSheet(ss, "Soundbox_Template", getSBHeaders());
      if (!data.sb.CREATED_DATE) data.sb.CREATED_DATE = nowStr;
      appendDataRow(sbSheet, data.sb, getSBHeaders());
    } else if (data.type === "lead") {
      var leadSheet = getOrCreateSheet(ss, "Leads_Template", getLeadHeaders());
      if (!data.lead.CREATED_DATE) data.lead.CREATED_DATE = nowStr;
      if (!data.lead.UPDATED_DATE) data.lead.UPDATED_DATE = nowStr;
      appendDataRow(leadSheet, data.lead, getLeadHeaders());
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
