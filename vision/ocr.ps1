$ErrorActionPreference = 'Stop'
$imagePath = $args[0]

# 1. Load Windows Runtime (WinRT) class types dynamically
$StorageFileClass = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$BitmapDecoderClass = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
$OcrEngineClass = [Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType = WindowsRuntime]

try {
    # 2. Open the image file asynchronously
    $fileAsync = $StorageFileClass::GetFileFromPathAsync($imagePath)
    while (-not $fileAsync.IsCompleted) { Start-Sleep -Milliseconds 5 }
    $file = $fileAsync.GetResults()

    # 3. Open stream for read
    $streamAsync = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read)
    while (-not $streamAsync.IsCompleted) { Start-Sleep -Milliseconds 5 }
    $stream = $streamAsync.GetResults()

    # 4. Decode bitmap
    $decoderAsync = $BitmapDecoderClass::CreateAsync($stream)
    while (-not $decoderAsync.IsCompleted) { Start-Sleep -Milliseconds 5 }
    $decoder = $decoderAsync.GetResults()

    $bitmapAsync = $decoder.GetSoftwareBitmapAsync()
    while (-not $bitmapAsync.IsCompleted) { Start-Sleep -Milliseconds 5 }
    $bitmap = $bitmapAsync.GetResults()

    # 5. Initialize OCR Engine and analyze
    $engine = $OcrEngineClass::TryCreateFromUserProfileLanguages()
    if ($null -eq $engine) {
        Write-Output "OCR Error: OCR Engine could not be created."
        exit 1
    }

    $ocrAsync = $engine.RecognizeAsync($bitmap)
    while (-not $ocrAsync.IsCompleted) { Start-Sleep -Milliseconds 5 }
    $ocrResult = $ocrAsync.GetResults()

    Write-Output $ocrResult.Text
} catch {
    Write-Output "OCR Error: $_"
    exit 1
}
