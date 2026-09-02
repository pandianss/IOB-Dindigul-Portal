[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$url = "https://script.google.com/macros/s/AKfycby_RxcPyViFLY_ILWqzxB6jb9RopXU_vZhHbusPdbrj70FcQx6vGcyrAQTTy_gW4goL/exec"
Write-Host "Fetching data from backend..."
$jsonContent = Invoke-RestMethod -Uri $url -Method Get

$qrList = $jsonContent.qr
$sbList = $jsonContent.sb
$leadList = $jsonContent.lead

$rows = @()

if ($qrList) {
    foreach ($item in $qrList) {
        $rows += [PSCustomObject]@{
            "Category" = "QR Code"
            "ID" = $item.ID
            "Timestamp" = $item.TIMESTAMP
            "Merchant_Name" = $item.MERCHANT_NAME
            "Account_Number" = $item.ACCOUNT_NO
            "Contact_Mobile" = $item.CONTACT_MOBILE
            "SOL_ID" = $item.SOL_ID
            "Branch_Name" = $item.BRANCH_NAME
            "District" = $item.DISTRICT
            "Staff_Roll" = $item.STAFF_ROLL
            "Staff_Name" = $item.STAFF_NAME
            "Staff_Mobile" = $item.STAFF_MOBILE
            "Staff_Designation" = $item.STAFF_DESIGNATION
            "Soundbox_Needed" = $item.SOUNDBOX_NEEDED
            "Status" = $item.STATUS
            "VPA" = $item.VPA
            "File_URL" = $item.FILE_URL
            "Vendor_Remarks" = $item.VENDOR_REMARKS
            "Completed_At" = $item.COMPLETED_AT
        }
    }
}

if ($sbList) {
    foreach ($item in $sbList) {
        $rows += [PSCustomObject]@{
            "Category" = "Soundbox"
            "ID" = $item.ID
            "Timestamp" = $item.TIMESTAMP
            "Merchant_Name" = $item.MERCHANT_NAME
            "Account_Number" = $item.ACCOUNT_NO
            "Contact_Mobile" = $item.CONTACT_MOBILE
            "SOL_ID" = $item.SOL_ID
            "Branch_Name" = $item.BRANCH_NAME
            "District" = $item.DISTRICT
            "Staff_Roll" = $item.STAFF_ROLL
            "Staff_Name" = $item.STAFF_NAME
            "Staff_Mobile" = $item.STAFF_MOBILE
            "Staff_Designation" = $item.STAFF_DESIGNATION
            "Soundbox_Needed" = "YES"
            "Status" = $item.STATUS
            "VPA" = $item.VPA
            "File_URL" = $item.FILE_URL
            "Vendor_Remarks" = $item.VENDOR_REMARKS
            "Completed_At" = $item.COMPLETED_AT
        }
    }
}

if ($leadList) {
    foreach ($item in $leadList) {
        $rows += [PSCustomObject]@{
            "Category" = "Product Lead"
            "ID" = $item.ID
            "Timestamp" = $item.TIMESTAMP
            "Merchant_Name" = $item.MERCHANT_NAME
            "Account_Number" = $item.ACCOUNT_NO
            "Contact_Mobile" = $item.CONTACT_MOBILE
            "SOL_ID" = $item.SOL_ID
            "Branch_Name" = $item.BRANCH_NAME
            "District" = $item.DISTRICT
            "Staff_Roll" = $item.STAFF_ROLL
            "Staff_Name" = $item.STAFF_NAME
            "Staff_Mobile" = $item.STAFF_MOBILE
            "Staff_Designation" = $item.STAFF_DESIGNATION
            "Soundbox_Needed" = ""
            "Status" = $item.STATUS
            "VPA" = ""
            "File_URL" = ""
            "Vendor_Remarks" = $item.VENDOR_REMARKS
            "Completed_At" = $item.COMPLETED_AT
        }
    }
}

$outputPath = "c:\Users\sspan\OneDrive\Desktop\snapshot\DigitalDindigul\iob_dindigul_applications_data.csv"
$rows | Export-Csv -Path $outputPath -NoTypeInformation -Encoding UTF8
Write-Host "Export completed successfully: $($rows.Count) rows saved to $outputPath"
