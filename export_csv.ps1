[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$url = "https://script.google.com/macros/s/AKfycby_RxcPyViFLY_ILWqzxB6jb9RopXU_vZhHbusPdbrj70FcQx6vGcyrAQTTy_gW4goL/exec"
Write-Host "Fetching data from backend..."
$data = Invoke-RestMethod -Uri $url -Method Get

$staffDict = @{}
if (Test-Path "staff_list.csv") {
    Import-Csv -Path "staff_list.csv" | ForEach-Object {
        if ($_.roll_no) {
            $staffDict[$_.roll_no.Trim()] = $_
        }
    }
}

$branchesDict = @{}
if (Test-Path "branches.csv") {
    Import-Csv -Path "branches.csv" | ForEach-Object {
        if ($_.code) {
            $branchesDict[$_.code.Trim().PadLeft(4, '0')] = $_
        }
    }
}

$rows = @()

if ($data.qr) {
    foreach ($item in $data.qr) {
        $sol = if ($item.SOL_ID) { $item.SOL_ID.ToString().PadLeft(4, '0') } else { "" }
        $b = if ($sol -and $branchesDict.ContainsKey($sol)) { $branchesDict[$sol] } else { $null }
        $branchName = if ($b) { $b.name_en } else { if ($item.BRANCH_NAME) { $item.BRANCH_NAME } else { if ($sol) { "Branch $sol" } else { "" } } }
        $district = if ($item.DISTRICT) { $item.DISTRICT } else { if ($b) { $b.district } else { "" } }
        
        $roll = if ($item.STAFF_ROLL) { $item.STAFF_ROLL.ToString().Trim() } else { "" }
        $st = if ($roll -and $staffDict.ContainsKey($roll)) { $staffDict[$roll] } else { $null }
        $staffName = if ($item.STAFF_NAME) { $item.STAFF_NAME } else { if ($st) { $st.name } else { "" } }
        $staffDesig = if ($st) { $st.designation } else { "" }
        $staffMob = if ($st) { $st.mobile } else { "" }

        $rows += [PSCustomObject]@{
            "Category" = "Merchant QR"
            "Status" = if ($item.STATUS) { $item.STATUS } else { "Pending Review" }
            "Merchant_Entity_Name" = $item.MERCHANTNAME
            "Account_Number" = $item.ACCOUNTNO
            "IFSC_Code" = $item.IFSC
            "VPA_UPI_ID" = $item.MERCHANTVPA
            "Mobile_Number" = $item.MOBILENO
            "Email_ID" = $item.EMAILID
            "GST_Number" = $item.GSTNO
            "Merchant_Type" = $item.MERCHANTTYPE
            "MCC_Code" = $item.MCCCODE
            "Latitude" = $item.LATITUDE
            "Longitude" = $item.LONGITUDE
            "Address_Line_1" = $item.ADDRESS1
            "Address_Line_2" = $item.ADDRESS2
            "Post_Office_City" = $item.POSTOFFICENAME
            "PIN_Code" = $item.PINCODE
            "State" = if ($item.STATE) { $item.STATE } else { "TamilNadu" }
            "District" = $district
            "Sub_District_Taluk" = $item.SUBDISTRICT
            "SOL_ID" = $sol
            "Branch_Name" = $branchName
            "Region" = "Dindigul"
            "Soundbox_Required" = $item.SOUNDBOX_REQUIRED
            "Soundbox_Language" = $item.SOUNDBOX_LANG
            "Product_Lead" = ""
            "No_Of_Devices" = ""
            "Contact_Person" = ""
            "Contact_Mobile" = ""
            "Staff_Roll_No" = $roll
            "Staff_Name" = $staffName
            "Staff_Designation" = $staffDesig
            "Staff_Mobile" = $staffMob
            "QR_PDF_URL" = $item.QR_PDF_URL
            "Vendor_Remarks" = $item.VENDOR_REMARKS
            "Created_Date" = $item.TIMESTAMP
            "Completed_Date" = $item.COMPLETED_DATE
        }
    }
}

if ($data.sb) {
    foreach ($item in $data.sb) {
        $sol = if ($item.SOL_ID) { $item.SOL_ID.ToString().PadLeft(4, '0') } else { "" }
        $b = if ($sol -and $branchesDict.ContainsKey($sol)) { $branchesDict[$sol] } else { $null }
        $branchName = if ($b) { $b.name_en } else { if ($item.BRANCH_NAME) { $item.BRANCH_NAME } else { if ($sol) { "Branch $sol" } else { "" } } }
        $district = if ($item.CITY) { $item.CITY } else { if ($b) { $b.district } else { "" } }
        
        $roll = if ($item.STAFF_ROLL) { $item.STAFF_ROLL.ToString().Trim() } else { "" }
        $st = if ($roll -and $staffDict.ContainsKey($roll)) { $staffDict[$roll] } else { $null }
        $staffName = if ($item.STAFF_NAME) { $item.STAFF_NAME } else { if ($st) { $st.name } else { "" } }
        $staffDesig = if ($st) { $st.designation } else { "" }
        $staffMob = if ($st) { $st.mobile } else { "" }

        $rows += [PSCustomObject]@{
            "Category" = "Soundbox"
            "Status" = if ($item.STATUS) { $item.STATUS } else { "Pending Review" }
            "Merchant_Entity_Name" = $item.ACCOUNT_NAME
            "Account_Number" = $item.ACCOUNT_NO
            "IFSC_Code" = ""
            "VPA_UPI_ID" = $item.VPA
            "Mobile_Number" = $item.MOBILE_NUMBER
            "Email_ID" = $item.EMAILID
            "GST_Number" = $item.GSTNO
            "Merchant_Type" = ""
            "MCC_Code" = $item.MCC
            "Latitude" = $item.LATITUDE
            "Longitude" = $item.LONGITUDE
            "Address_Line_1" = $item.ADDRESS
            "Address_Line_2" = ""
            "Post_Office_City" = $item.CITY
            "PIN_Code" = $item.PIN_CODE
            "State" = if ($item.STATE) { $item.STATE } else { "TamilNadu" }
            "District" = $district
            "Sub_District_Taluk" = ""
            "SOL_ID" = $sol
            "Branch_Name" = $branchName
            "Region" = if ($item.REGION) { $item.REGION } else { "Dindigul" }
            "Soundbox_Required" = "Yes"
            "Soundbox_Language" = $item.LANGUAGE
            "Product_Lead" = ""
            "No_Of_Devices" = ""
            "Contact_Person" = ""
            "Contact_Mobile" = ""
            "Staff_Roll_No" = $roll
            "Staff_Name" = $staffName
            "Staff_Designation" = $staffDesig
            "Staff_Mobile" = $staffMob
            "QR_PDF_URL" = $item.QR_PDF_URL
            "Vendor_Remarks" = $item.VENDOR_REMARKS
            "Created_Date" = $item.TIMESTAMP
            "Completed_Date" = $item.COMPLETED_DATE
        }
    }
}

if ($data.lead) {
    foreach ($item in $data.lead) {
        $sol = if ($item.SOL_ID) { $item.SOL_ID.ToString().PadLeft(4, '0') } else { "" }
        $b = if ($sol -and $branchesDict.ContainsKey($sol)) { $branchesDict[$sol] } else { $null }
        $branchName = if ($b) { $b.name_en } else { if ($item.BRANCH_NAME) { $item.BRANCH_NAME } else { if ($sol) { "Branch $sol" } else { "" } } }
        $district = if ($b) { $b.district } else { "" }
        
        $roll = if ($item.STAFF_ROLL) { $item.STAFF_ROLL.ToString().Trim() } else { "" }
        $st = if ($roll -and $staffDict.ContainsKey($roll)) { $staffDict[$roll] } else { $null }
        $staffName = if ($item.STAFF_NAME) { $item.STAFF_NAME } else { if ($st) { $st.name } else { "" } }
        $staffDesig = if ($st) { $st.designation } else { "" }
        $staffMob = if ($st) { $st.mobile } else { "" }

        $rows += [PSCustomObject]@{
            "Category" = "Product Lead"
            "Status" = if ($item.STATUS) { $item.STATUS } else { "Pending Review" }
            "Merchant_Entity_Name" = $item.MERCHANT_NAME
            "Account_Number" = $item.ACCOUNT_NO
            "IFSC_Code" = ""
            "VPA_UPI_ID" = ""
            "Mobile_Number" = $item.MOBILE_NO
            "Email_ID" = $item.EMAILID
            "GST_Number" = $item.GSTNO
            "Merchant_Type" = ""
            "MCC_Code" = ""
            "Latitude" = $item.LATITUDE
            "Longitude" = $item.LONGITUDE
            "Address_Line_1" = $item.ADDRESS
            "Address_Line_2" = ""
            "Post_Office_City" = ""
            "PIN_Code" = ""
            "State" = "TamilNadu"
            "District" = $district
            "Sub_District_Taluk" = ""
            "SOL_ID" = $sol
            "Branch_Name" = $branchName
            "Region" = "Dindigul"
            "Soundbox_Required" = ""
            "Soundbox_Language" = ""
            "Product_Lead" = $item.PRODUCT
            "No_Of_Devices" = $item.NO_OF_DEVICES
            "Contact_Person" = $item.CONTACT_NAME
            "Contact_Mobile" = $item.CONTACT_MOBILE
            "Staff_Roll_No" = $roll
            "Staff_Name" = $staffName
            "Staff_Designation" = $staffDesig
            "Staff_Mobile" = $staffMob
            "QR_PDF_URL" = ""
            "Vendor_Remarks" = $item.VENDOR_REMARKS
            "Created_Date" = if ($item.UPDATED_DATE) { $item.UPDATED_DATE } else { $item.TIMESTAMP }
            "Completed_Date" = $item.COMPLETED_DATE
        }
    }
}

$outputPath = "c:\Users\sspan\OneDrive\Desktop\snapshot\DigitalDindigul\iob_dindigul_applications_data.csv"
$rows | Export-Csv -Path $outputPath -NoTypeInformation -Encoding UTF8
Write-Host "SUCCESS: Exported $($rows.Count) applications with all columns including Email, Latitude, Longitude, Address, GST, MCC, Staff info to $outputPath"
