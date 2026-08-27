@echo off
chcp 65001 >nul
REM ============================================================
REM 独立站商品监控 Agent - Windows 一键启动
REM 使用方法：双击本文件即可
REM ============================================================
title 独立站商品监控 Agent

set SCRIPT_DIR=%~dp0
set BIN=%SCRIPT_DIR%monitor-windows.exe

if not exist "%BIN%" (
  echo 未找到程序文件: %BIN%
  echo 请确认 monitor-windows.exe 与本脚本在同一个文件夹。
  pause
  exit /b 1
)

echo ===========================================
echo   独立站商品监控 Agent 启动中...
echo ===========================================
echo 启动 WebUI，浏览器将自动打开 http://127.0.0.1:8321
echo 关闭本窗口 = 停止监控
echo ===========================================

"%BIN%" web

echo.
echo 监控已停止。
pause