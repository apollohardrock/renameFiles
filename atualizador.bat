@echo off
echo =========================================
echo   Atualizando o aplicativo RenameFiles...
echo =========================================
echo.

echo 1. Limpando a memoria travada do Windows...
del "%temp%\_MEI*" /F /S /Q >nul 2>&1

echo 2. Baixando a versao nova e atualizada...
curl -L -o "RenameFiles.exe" "https://github.com/apollohardrock/renameFiles/releases/latest/download/renameFiles.exe"

echo.
echo =========================================
echo PRONTO! O app foi atualizado. 
echo Pode fechar essa tela e usar o aplicativo novo!
echo =========================================
pause