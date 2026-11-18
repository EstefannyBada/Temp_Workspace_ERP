@echo off
TITLE ERP Django - Iniciando Sesion
COLOR 0A

:: ── 1. RUTAS DINÁMICAS ────────────────────────────────────────────────────
SET USB_PATH=%~dp0
SET PC_WORK=C:\Temp_Workspace_ERP

:: ── 2. CREAR TALLER EN DISCO LOCAL ────────────────────────────────────────
echo ======================================================
echo  ERP DJANGO :: USB ^-^> PC
echo  USB: %USB_PATH%
echo  PC:  %PC_WORK%
echo ======================================================
if not exist "%PC_WORK%" (
    mkdir "%PC_WORK%"
    echo [OK] Carpeta creada: %PC_WORK%
)

:: ── 3. SINCRONIZAR USB → PC (solo archivos nuevos o modificados) ───────────
echo Sincronizando proyecto a la PC...
xcopy /s /e /y /d "%USB_PATH%WorkSpace_ERP" "%PC_WORK%" >nul 2>&1
echo [OK] Sincronizacion completada.

:: ── 4. CONFIGURAR PATH TEMPORAL ───────────────────────────────────────────
SET PATH=%USB_PATH%Python_Portable;%USB_PATH%Python_Portable\Scripts;%USB_PATH%Git_Portable\bin;%PATH%

:: ── 5. RECREAR ENTORNO VIRTUAL SI NO EXISTE EN PC ─────────────────────────
if not exist "%PC_WORK%\env_erp" (
    echo Creando entorno virtual en la PC...
    python -m virtualenv "%PC_WORK%\env_erp"
    if exist "%PC_WORK%\requirements.txt" (
        echo Instalando dependencias desde requirements.txt...
        "%PC_WORK%\env_erp\Scripts\python.exe" -m pip install -r "%PC_WORK%\requirements.txt" --quiet
    )
    echo [OK] Entorno virtual creado.
)

:: ── 6. ACTIVAR ENTORNO VIRTUAL ────────────────────────────────────────────
SET PATH=%PC_WORK%\env_erp\Scripts;%PATH%
echo [OK] Entorno virtual activo.

:: ── 7. IR A LA CARPETA DE TRABAJO ─────────────────────────────────────────
cd /d "%PC_WORK%"
echo.
echo VERSIONES ACTIVAS:
python --version
git --version
echo.
echo --- RECUERDA EJECUTAR finalizar_sesion.bat AL TERMINAR ---
cmd /k "echo ERP listo en %PC_WORK%"
