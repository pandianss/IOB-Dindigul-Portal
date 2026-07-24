# Google Sheets Backend Setup Guide (Apps Script v2.3)

Follow these steps to update your Google Sheet backend to support **Merchant Product Leads** (3-in-1 POS, IOB Pay, QR Standee).

---

## Step 1: Update Google Apps Script
1. Open your Google Sheet (**IOB Merchant Applications**).
2. Go to **Extensions → Apps Script**.
3. Replace all code in `Code.gs` with the updated code from [Google_Apps_Script_v2.gs](file:///C:/Users/sspan/Videos/Form/Google_Apps_Script_v2.gs):

```javascript
function doGet(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var result = { qr: [], sb: [], lead: [] };

  var qrSheet = ss.getSheetByName("QR_Template");
  if (qrSheet) {
    var qrData = qrSheet.getDataRange().getValues();
    if (qrData.length > 1) {
      var headers = qrData[0];
      for (var i = 1; i < qrData.length; i++) {
        var row = qrData[i];
        var item = { rowIndex: i + 1 };
        for (var j = 0; j < headers.length; j++) {
          item[headers[j]] = row[j];
        }
        result.qr.push(item);
      }
    }
  }

  var sbSheet = ss.getSheetByName("Soundbox_Template");
  if (sbSheet) {
    var sbData = sbSheet.getDataRange().getValues();
    if (sbData.length > 1) {
      var headers = sbData[0];
      for (var i = 1; i < sbData.length; i++) {
        var row = sbData[i];
        var item = { rowIndex: i + 1 };
        for (var j = 0; j < headers.length; j++) {
          item[headers[j]] = row[j];
        }
        result.sb.push(item);
      }
    }
  }

  var leadSheet = ss.getSheetByName("Leads_Template");
  if (leadSheet) {
    var leadData = leadSheet.getDataRange().getValues();
    if (leadData.length > 1) {
      var headers = leadData[0];
      for (var i = 1; i < leadData.length; i++) {
        var row = leadData[i];
        var item = { rowIndex: i + 1 };
        for (var j = 0; j < headers.length; j++) {
          item[headers[j]] = row[j];
        }
        result.lead.push(item);
      }
    }
  }

  return ContentService.createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var ss = SpreadsheetApp.getActiveSpreadsheet();

    if (data.action === "updateStatus") {
      var sheet = ss.getSheetByName(data.sheetName);
      if (!sheet) throw new Error("Sheet not found: " + data.sheetName);

      var rowIndex = parseInt(data.rowIndex);
      var pdfUrl = "";

      if (data.pdfBase64) {
        var folderName = "IOB_QR_PDFs";
        var folders = DriveApp.getFoldersByName(folderName);
        var folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);
        
        var blob = Utilities.newBlob(
          Utilities.base64Decode(data.pdfBase64),
          "application/pdf",
          data.pdfName || ("Document_" + rowIndex + ".pdf")
        );
        var file = folder.createFile(blob);
        file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
        pdfUrl = file.getUrl();
      }

      var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
      var statusCol = headers.indexOf("STATUS") + 1;
      var dateCol = headers.indexOf("COMPLETED_DATE") + 1;
      var pdfCol = headers.indexOf("QR_PDF_URL") + 1;
      var vpaCol = headers.indexOf("MERCHANTVPA") + 1;

      var nowFormatted = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm");

      if (statusCol > 0) sheet.getRange(rowIndex, statusCol).setValue(data.status || "Completed");
      if (dateCol > 0) sheet.getRange(rowIndex, dateCol).setValue(nowFormatted);
      if (pdfCol > 0 && pdfUrl) sheet.getRange(rowIndex, pdfCol).setValue(pdfUrl);
      if (vpaCol > 0 && data.vpa) sheet.getRange(rowIndex, vpaCol).setValue(data.vpa);

      if (data.sheetName === "QR_Template" && data.soundboxRequired === "Yes") {
        var qrRowData = sheet.getRange(rowIndex, 1, 1, headers.length).getValues()[0];
        var qrObj = {};
        for (var k = 0; k < headers.length; k++) {
          qrObj[headers[k]] = qrRowData[k];
        }

        var finalVpa = data.vpa || qrObj.MERCHANTVPA;

        var sbSheet = ss.getSheetByName("Soundbox_Template");
        if (!sbSheet) {
          sbSheet = ss.insertSheet("Soundbox_Template");
          sbSheet.appendRow([
            "Sol ID", "Branch Name", "Region", "VPA", "Account Name",
            "Address", "Pin Code", "City", "State", "MCC",
            "Mobile Number", "Language", "STATUS", "COMPLETED_DATE", "QR_PDF_URL"
          ]);
          sbSheet.getRange(1, 1, 1, 15).setFontWeight("bold").setBackground("#1a3a7a").setFontColor("#ffffff");
        }

        var fullAddr = (qrObj.ADDRESS1 || "") + (qrObj.ADDRESS2 ? ", " + qrObj.ADDRESS2 : "");

        sbSheet.appendRow([
          "'" + (data.solId || qrObj.SOL_ID || ""),
          "",
          "Dindigul",
          finalVpa,
          qrObj.MERCHANTNAME,
          fullAddr,
          "'" + qrObj.PINCODE,
          qrObj.DISTRICT,
          qrObj.STATE,
          "'" + qrObj.MCCCODE,
          "'" + qrObj.MOBILENO,
          data.soundboxLang || qrObj.SOUNDBOX_LANG || "ta",
          "Pending",
          "",
          ""
        ]);
      }

      return ContentService.createTextOutput(JSON.stringify({ status: "success", pdfUrl: pdfUrl }))
        .setMimeType(ContentService.MimeType.JSON);
    }

    if (data.qr) {
      var qrSheet = ss.getSheetByName("QR_Template");
      if (!qrSheet) {
        qrSheet = ss.insertSheet("QR_Template");
        qrSheet.appendRow([
          "MERCHANTNAME", "MERCHANTVPA", "ACCOUNTNO", "IFSC", "MOBILENO",
          "MCCCODE", "ACTIVE", "ONBORDINGTYPE", "GSTNO", "EMAILID",
          "MERCHANTTYPE", "LATITUDE", "LONGITUDE", "ADDRESS1", "ADDRESS2",
          "POSTOFFICENAME", "PINCODE", "STATE", "DISTRICT", "SUBDISTRICT",
          "SOUNDBOX_REQUIRED", "SOL_ID", "SOUNDBOX_LANG",
          "STATUS", "COMPLETED_DATE", "QR_PDF_URL"
        ]);
        qrSheet.getRange(1, 1, 1, 26).setFontWeight("bold").setBackground("#1a3a7a").setFontColor("#ffffff");
      }
      var qr = data.qr;
      qrSheet.appendRow([
        qr.MERCHANTNAME, qr.MERCHANTVPA, "'" + qr.ACCOUNTNO, qr.IFSC, "'" + qr.MOBILENO,
        "'" + qr.MCCCODE, qr.ACTIVE, qr.ONBORDINGTYPE, qr.GSTNO, qr.EMAILID,
        qr.MERCHANTTYPE, qr.LATITUDE, qr.LONGITUDE, qr.ADDRESS1, qr.ADDRESS2,
        qr.POSTOFFICENAME, "'" + qr.PINCODE, qr.STATE, qr.DISTRICT, qr.SUBDISTRICT,
        qr.SOUNDBOX_REQUIRED, "'" + (qr.SOL_ID || ""), qr.SOUNDBOX_LANG || "",
        "Pending", "", ""
      ]);
    }

    if (data.sb) {
      var sbSheet = ss.getSheetByName("Soundbox_Template");
      if (!sbSheet) {
        sbSheet = ss.insertSheet("Soundbox_Template");
        sbSheet.appendRow([
          "Sol ID", "Branch Name", "Region", "VPA", "Account Name",
          "Address", "Pin Code", "City", "State", "MCC",
          "Mobile Number", "Language", "STATUS", "COMPLETED_DATE", "QR_PDF_URL"
        ]);
        sbSheet.getRange(1, 1, 1, 15).setFontWeight("bold").setBackground("#1a3a7a").setFontColor("#ffffff");
      }
      var sb = data.sb;
      sbSheet.appendRow([
        "'" + sb.SOL_ID, sb.BRANCH_NAME, "Dindigul", sb.VPA, sb.ACCOUNT_NAME,
        sb.ADDRESS, "'" + sb.PIN_CODE, sb.CITY, sb.STATE, "'" + sb.MCC,
        "'" + sb.MOBILE_NUMBER, sb.LANGUAGE, "Pending", "", ""
      ]);
    }

    if (data.lead) {
      var leadSheet = ss.getSheetByName("Leads_Template");
      if (!leadSheet) {
        leadSheet = ss.insertSheet("Leads_Template");
        leadSheet.appendRow([
          "PRODUCT", "SOL_ID", "BRANCH_NAME", "ACCOUNT_NO", "MERCHANT_NAME",
          "MOBILE_NO", "NO_OF_DEVICES", "CONTACT_NAME", "CONTACT_MOBILE",
          "STATUS", "SUBMISSION_DATE", "COMPLETED_DATE", "QR_PDF_URL"
        ]);
        leadSheet.getRange(1, 1, 1, 13).setFontWeight("bold").setBackground("#1a3a7a").setFontColor("#ffffff");
      }
      var lead = data.lead;
      var subDate = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm");
      leadSheet.appendRow([
        lead.PRODUCT, "'" + lead.SOL_ID, lead.BRANCH_NAME, "'" + lead.ACCOUNT_NO, lead.MERCHANT_NAME,
        "'" + lead.MOBILE_NO, lead.NO_OF_DEVICES, lead.CONTACT_NAME, "'" + lead.CONTACT_MOBILE,
        "Pending", subDate, "", ""
      ]);
    }

    return ContentService.createTextOutput(JSON.stringify({ status: "success" }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ status: "error", message: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
```

---

## Step 2: Publish / Deploy New Version
1. Click **Deploy → Manage deployments**.
2. Click the edit icon ✏️ next to your active deployment.
3. Under **Version**, select **New version**.
4. Click **Deploy**.
