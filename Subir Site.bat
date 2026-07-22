@echo off
title Publicar Controle de Rotinas

cd /d "C:\Users\valdeir.vaz\Desktop\Controle_Rotinas"

echo =========================================
echo      PUBLICANDO O CONTROLE DE ROTINAS
echo =========================================
echo.

git add .

set /p MSG=Digite a mensagem da atualizacao: 

git commit -m "%MSG%"

if errorlevel 1 (
    echo.
    echo Nenhuma alteracao para enviar ou ocorreu um erro no commit.
    pause
    exit
)

git push

if errorlevel 1 (
    echo.
    echo Erro ao enviar para o GitHub.
    pause
    exit

)

echo.
echo =========================================
echo  PROJETO ENVIADO COM SUCESSO!
echo.
echo  O Render iniciara o deploy automaticamente.
echo =========================================

pause