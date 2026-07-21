@echo off
REM Script para subir alteracoes do projeto Controle_Rotinas para o GitHub/Render
REM Uso: subir.bat "mensagem do commit"

cd /d C:\Users\valdeir.vaz\Desktop\Controle_Rotinas

if "%~1"=="" (
    echo.
    echo Voce esqueceu de passar a mensagem do commit.
    echo Exemplo: subir.bat "Ajuste rotinas fixas"
    echo.
    pause
    exit /b 1
)

echo.
echo === Verificando status ===
git status

echo.
echo === Adicionando alteracoes ===
git add .

echo.
echo === Criando commit ===
git commit -m "%~1"

echo.
echo === Enviando para o GitHub (o Render vai fazer o deploy automatico) ===
git push

echo.
echo === Concluido! Acompanhe o deploy no Render. ===
pause
