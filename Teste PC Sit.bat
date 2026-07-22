@echo off

cd /d C:\Users\valdeir.vaz\Desktop\Controle_Rotinas

set "DATABASE_URL=postgresql://neondb_owner:npg_ygVliaF7GvK8@ep-autumn-star-awogk0qa-pooler.c-12.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

C:\Users\valdeir.vaz\AppData\Local\Python\pythoncore-3.14-64\python.exe app.py

pause