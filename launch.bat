@echo off
title SEO Brief Generator
echo ========================================
echo    SEO Brief Generator - Lancement
echo ========================================
echo.

cd /d "C:\Users\Guy Zitu\seo_brief_generator"

echo [1/2] Verification des dependances...
pip install -r requirements.txt -q

echo.
echo [2/2] Lancement de l'application...
echo.
echo L'application va s'ouvrir dans votre navigateur.
echo Pour arreter : Ctrl+C dans cette fenetre.
echo.

streamlit run app.py --server.port 8501 --browser.gatherUsageStats false

pause
