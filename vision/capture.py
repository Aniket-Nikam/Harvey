import mss
import base64
from PIL import Image

class ScreenCapturer:
    def __init__(self, config):
        self.config = config
    
    def capture(self):
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # primary
                screenshot = sct.grab(monitor)
                # mss returns BGRA
                img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
                return img
        except Exception as e:
            print(f"Screen capture error: {e}")
            return None
    
    def analyze(self, image):
        import os
        import subprocess
        
        if image is None:
            return "No screen content captured."
            
        temp_path = os.path.abspath("temp_screenshot.png")
        try:
            # Save the PIL Image to temporary file
            image.save(temp_path, format="PNG")
            
            # Get absolute path to the ocr.ps1 script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            ocr_script_path = os.path.join(current_dir, "ocr.ps1")
            
            # Run the script via subprocess
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ocr_script_path, temp_path],
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            
            # Clean up the temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            if result.returncode == 0:
                text = result.stdout.strip()
                if not text:
                    return "Screen context is empty (no text detected on screen)."
                return f"Visible screen text/code:\n{text}"
            else:
                return f"Failed to run local OCR: {result.stderr}"
        except Exception as e:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            return f"Failed to analyze screen context locally: {str(e)}"