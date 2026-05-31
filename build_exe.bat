@echo off
cd /d "%~dp0"
pyinstaller --noconfirm --clean --onefile --windowed \
    --add-data "client\login.ui;client" \
    --add-data "client\mainwindow.ui;client" \
    app_launcher.py

echo Build finished. The executable will be in the dist folder.
