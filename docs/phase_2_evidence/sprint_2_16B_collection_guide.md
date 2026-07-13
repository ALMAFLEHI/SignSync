# Sprint 2.16B Samsung A55 Collection And Pull Guide

## Collection Order

Follow this exact active V3 order:

1. deposit
2. withdraw
3. balance
4. account
5. card
6. pin
7. password
8. identity_verification
9. cash
10. payment
11. fee
12. loan
13. savings
14. open_account
15. close_account
16. fraud
17. block_card
18. help
19. confirm
20. statement
21. bill_payment
22. branch
23. cheque
24. interest_rate
25. credit_card
26. debit_card
27. lost_card
28. replace_card
29. change_pin
30. reset_password
31. refund
32. complaint
33. appointment
34. account_number
35. card_limit
36. daily_limit

## Recording Procedure

1. Select one label in the Sprint 2.16B collection page.
2. Start the camera.
3. Prepare the sign at normal final-demo phone distance with clear lighting.
4. Keep every required hand visible and use normal signing speed.
5. Tap **Capture and Save Sample** once.
6. Complete one 60-valid-frame sample.
7. Wait for the exact sample ID and save confirmation.
8. Repeat manually until that label reaches 25/25.
9. Select the next incomplete label and confirm the label change.
10. Include small natural variation without intentionally changing the sign.
11. Stop after 25/25. The page blocks additional captures for that label.

Do not uninstall the application, clear application storage, record alphabet/digit samples, or use the four protected pilot labels from this page. Only landmark JSON is saved; raw video is not stored.

## Android And PC Paths

Android source:

`/storage/emulated/0/Android/data/com.example.flutter_app/files/signsync_phone_samples/`

PC destination:

`ml/data_phone/landmark_samples/`

Discovered ADB executable:

`C:\Users\devls\AppData\Local\Android\Sdk\platform-tools\adb.exe`

## Hash-Safe PowerShell Pull Workflow

Run from the SignSync project root. The staging folder prevents `adb pull` from overwriting the protected PC copies.

```powershell
$adb = 'C:\Users\devls\AppData\Local\Android\Sdk\platform-tools\adb.exe'
$androidSource = '/storage/emulated/0/Android/data/com.example.flutter_app/files/signsync_phone_samples/.'
$staging = 'ml/data_phone/sprint_2_16B_pull_staging'
$destination = 'ml/data_phone/landmark_samples'

& $adb devices -l

if (Test-Path -LiteralPath $staging) {
    throw "Staging folder already exists. Review it instead of overwriting it: $staging"
}
New-Item -ItemType Directory -Path $staging | Out-Null
& $adb pull $androidSource $staging
if ($LASTEXITCODE -ne 0) { throw 'ADB pull failed.' }

$pulledFiles = Get-ChildItem -LiteralPath $staging -Filter '*.json' -File
foreach ($file in $pulledFiles) {
    $target = Join-Path $destination $file.Name
    if (Test-Path -LiteralPath $target) {
        $sourceHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        $targetHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
        if ($sourceHash -ne $targetHash) {
            throw "Hash conflict for existing protected file: $($file.Name)"
        }
        continue
    }
    Copy-Item -LiteralPath $file.FullName -Destination $target
}

(Get-ChildItem -LiteralPath $destination -Filter '*.json' -File).Count
```

Keep the staging folder until the checker passes and the final backup exists.

## Validation

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv-tflite\Lib\site-packages').Path
& 'C:\Users\devls\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' ml/src/check_sprint_2_16B_phone_samples.py
```

During collection, `PENDING` is expected. Final `PASS` requires pilot integrity, 900 valid new samples, 1,000 total banking samples, exactly 25 per intent, and zero invalid, duplicate, removed, alphabet, digit, or unexpected samples.

## Final Backup After PASS Only

Do not run this until the checker reports final PASS and the JSON count is exactly 1,000.

```powershell
$backup = 'ml/data_phone/sprint_2_16B_banking_phone_samples_1000_backup.zip'
if (Test-Path -LiteralPath $backup) {
    throw "Backup already exists and will not be overwritten: $backup"
}
$jsonCount = (Get-ChildItem -LiteralPath 'ml/data_phone/landmark_samples' -Filter '*.json' -File).Count
if ($jsonCount -ne 1000) { throw "Expected 1000 JSON files, found $jsonCount" }
Compress-Archive -Path 'ml/data_phone/landmark_samples/*.json' -DestinationPath $backup -CompressionLevel Optimal
```

Do not uninstall or clear the Android application before the pull, validation, and backup are complete.
