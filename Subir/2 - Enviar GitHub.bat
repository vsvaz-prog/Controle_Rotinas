@echo off
title Enviar Projeto

cd /d "C:\Users\valdeir.vaz\Desktop\Controle_Rotinas"

git add .

set /p msg=Mensagem do commit:

git commit -m "%msg%"

git push

pause