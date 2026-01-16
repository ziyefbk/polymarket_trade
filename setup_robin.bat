@echo off
REM Robin Integration Setup Script for Windows
REM 使用 conda 环境安装和测试 Robin 集成

echo ============================================================
echo Robin Integration Setup for Windows
echo ============================================================
echo.

REM Step 1: Activate conda environment
echo [1/4] Activating conda environment 'math'...
call conda activate math
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate conda environment 'math'
    echo Please make sure conda is installed and 'math' environment exists
    pause
    exit /b 1
)
echo OK: Conda environment activated
echo.

REM Step 2: Install Robin dependencies
echo [2/4] Installing Robin dependencies...
cd robin_signals
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    cd ..
    pause
    exit /b 1
)
cd ..
echo OK: Dependencies installed
echo.

REM Step 3: Setup .env file
echo [3/4] Setting up .env configuration...
if not exist "robin_signals\.env" (
    echo Creating .env from template...
    copy robin_signals\.env.example robin_signals\.env
    echo.
    echo IMPORTANT: Please edit robin_signals\.env and add your API keys:
    echo   - OPENAI_API_KEY=your_key_here
    echo   - ANTHROPIC_API_KEY=your_key_here
    echo   - GOOGLE_API_KEY=your_key_here
    echo   ^(At least one is required^)
    echo.
) else (
    echo .env file already exists
)
echo.

REM Step 4: Run setup test
echo [4/4] Running configuration test...
python test_robin_setup.py
echo.

echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo Next Steps:
echo 1. Install and start Tor: https://www.torproject.org/download/
echo 2. Edit robin_signals\.env with your API keys
echo 3. Run: python test_robin_setup.py
echo 4. Run example: python examples\robin_integration_example.py
echo.
echo For detailed documentation, see: docs\ROBIN_INTEGRATION.md
echo ============================================================
pause
