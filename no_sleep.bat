@echo off
REM Отключение сна и гибернации Windows
powercfg /x -standby-timeout-ac 0
powercfg /x -standby-timeout-dc 0
powercfg /x -hibernate-timeout-ac 0
powercfg /x -hibernate-timeout-dc 0
echo Сон Windows отключен.
pause