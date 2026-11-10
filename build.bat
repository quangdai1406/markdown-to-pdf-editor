@echo off
pip install -r requirements.txt
python -m PyInstaller --noconfirm --onefile --windowed --name PressworkPDF --add-data "marked.umd.js;." --add-data "ui.html;." presswork_pdf.py
echo Done. See dist\PressworkPDF.exe
