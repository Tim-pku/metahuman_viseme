@echo off
chcp 65001

call .\venv\python.exe semantic_server.py

@echo 请按任意键继续
call pause