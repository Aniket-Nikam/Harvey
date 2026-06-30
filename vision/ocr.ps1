$ErrorActionPreference = 'Stop'
$imagePath = $args[0]

$source = @"
using System;
using System.IO;
using System.Threading.Tasks;
using Windows.Storage;
using Windows.Graphics.Imaging;
using Windows.Media.Ocr;

public class OcrHelper {
    public static string Recognize(string imagePath) {
        try {
            var file = StorageFile.GetFileFromPathAsync(imagePath).GetAwaiter().GetResult();
            var stream = file.OpenAsync(FileAccessMode.Read).GetAwaiter().GetResult();
            var decoder = BitmapDecoder.CreateAsync(stream).GetAwaiter().GetResult();
            var bitmap = decoder.GetSoftwareBitmapAsync().GetAwaiter().GetResult();
            var engine = OcrEngine.TryCreateFromUserProfileLanguages();
            if (engine == null) {
                return "OCR Error: OCR Engine could not be created (check if language packs are installed).";
            }
            var result = engine.RecognizeAsync(bitmap).GetAwaiter().GetResult();
            return result.Text;
        } catch (Exception e) {
            return "OCR Error: " + e.Message;
        }
    }
}
"@

Add-Type -TypeDefinition $source -ReferencedAssemblies @(
    "System.Runtime.WindowsRuntime",
    "C:\Windows\System32\WinMetadata\Windows.Foundation.winmd",
    "C:\Windows\System32\WinMetadata\Windows.Storage.winmd",
    "C:\Windows\System32\WinMetadata\Windows.Graphics.winmd",
    "C:\Windows\System32\WinMetadata\Windows.Media.winmd"
)

[OcrHelper]::Recognize($imagePath)
