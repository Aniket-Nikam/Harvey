@echo off
pip install -r requirements.txt
pyinstaller --onefile --noconsole --add-data "config.yaml;." --hidden-import=groq --hidden-import=whisper main.py
echo Build complete. Use --obfuscate for more stealth if available.