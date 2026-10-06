@echo off
set LOG_FILE=C:\Windows\Temp\Deploy_GLPI_Agent.log
set MSI_PATH=\\SERVIDOR_TI\Deploy\GLPI-Agent-1.20-x64.msi
set SERVER_URL=http://flowagente.floripa.sc.gov.br:8000/inventory

echo %date% %time% - Iniciando verificacao do GLPI Agent via GPO. >> "%LOG_FILE%"

if exist "C:\Program Files\GLPI-Agent\glpi-agent.bat" goto INSTALADO
if exist "C:\Program Files\GLPI-Agent\glpi-agent-core.bat" goto INSTALADO

echo %date% %time% - Agente nao encontrado. Iniciando instalacao silenciosa... >> "%LOG_FILE%"
msiexec.exe /i "%MSI_PATH%" /quiet /norestart SERVER="%SERVER_URL%" RUNNOW=1 ADD_FIREWALL_EXCEPTION=1

if "%ERRORLEVEL%"=="0" goto CONCLUIDA
if "%ERRORLEVEL%"=="3010" goto CONCLUIDA

echo %date% %time% - Falha na instalacao. Codigo msiexec %ERRORLEVEL%. >> "%LOG_FILE%"
exit /b %ERRORLEVEL%

:CONCLUIDA
echo %date% %time% - Instalacao concluida. >> "%LOG_FILE%"
goto FIM

:INSTALADO
echo %date% %time% - Ja estava instalado. Nenhuma acao necessaria. >> "%LOG_FILE%"

:FIM
exit /b 0
