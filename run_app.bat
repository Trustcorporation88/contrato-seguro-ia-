@echo off
REM Script para executar ContratoSeguro AI
REM Compatível com Windows PowerShell e CMD

title ContratoSeguro AI v2.0

echo.
echo ============================================
echo   ContratoSeguro AI v2.0
echo   Iniciando aplicacao...
echo ============================================
echo.

REM Mudar para o diretório do projeto
cd /d "%~dp0"

REM Executar Streamlit
python -m streamlit run app.py

pause
