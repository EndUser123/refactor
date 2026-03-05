@echo off
REM Refactor Skill - Windows Junction Installation Script
REM
REM This script creates a junction from P:/.claude/skills/refactor
REM to the current directory (refactor skill repository).
REM
REM Junctions are recommended on Windows because:
REM - No admin privileges required
REM - Git-compatible (unlike symlinks)
REM - Automatic updates when editing in package directory
REM
REM Usage: Run from repository root as administrator if needed

setlocal

echo ========================================
echo Refactor Skill - Dev Installation
echo ========================================
echo.

REM Get current directory (repository root)
set "REPO_ROOT=%CD%"

REM Target junction location
set "TARGET_DIR=P:\.claude\skills\refactor"

REM Check if target directory exists
if exist "%TARGET_DIR%" (
    echo WARNING: Target directory already exists: %TARGET_DIR%
    echo.
    choice /C YN /M "Do you want to remove and recreate the junction"
    if errorlevel 2 (
        echo Installation cancelled.
        pause
        exit /b 1
    )

    echo Removing existing junction...
    rmdir "%TARGET_DIR%" 2>nul
    if errorlevel 1 (
        echo ERROR: Failed to remove existing directory.
        echo        It might not be a junction or files are in use.
        pause
        exit /b 1
    )
)

REM Create parent directory if it doesn't exist
if not exist "P:\.claude\skills\" (
    echo Creating parent directory: P:\.claude\skills\
    mkdir "P:\.claude\skills"
    if errorlevel 1 (
        echo ERROR: Failed to create parent directory.
        pause
        exit /b 1
    )
)

REM Create junction
echo.
echo Creating junction:
echo   From: %TARGET_DIR%
echo   To:   %REPO_ROOT%\skill
echo.

mklink /J "%TARGET_DIR%" "%REPO_ROOT%\skill"

if errorlevel 1 (
    echo.
    echo ERROR: Failed to create junction.
    echo.
    echo Possible solutions:
    echo   1. Run this script as Administrator
    echo   2. Verify P:\ drive exists and is accessible
    echo   3. Check permissions on P:\.claude\skills\
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation successful!
echo ========================================
echo.
echo The refactor skill is now available at:
echo   %TARGET_DIR%
echo.
echo You can now invoke the skill from Claude Code:
echo   /refactor
echo.
echo To verify the junction works, run:
echo   dir "%TARGET_DIR%"
echo.
echo To uninstall, run:
echo   rmdir "%TARGET_DIR%"
echo.
pause
