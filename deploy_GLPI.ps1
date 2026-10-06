$Log = 'C:\Windows\Temp\Deploy_GLPI_Agent.log'
$Msi = '\\SERVIDOR_TI\Deploy\GLPI-Agent-1.20-x64.msi'
$ServerUrl = 'http://flowagente.floripa.sc.gov.br:8000/inventory'

function Write-Log($Message) {
    $Timestamp = Get-Date -Format 'dd/MM/yyyy HH:mm:ss'
    "$Timestamp - $Message" | Out-File -FilePath $Log -Append -Encoding UTF8
}

Write-Log 'Iniciando verificacao do GLPI Agent via GPO.'

$instalado = (Test-Path 'C:\Program Files\GLPI-Agent\glpi-agent.bat') -or (Test-Path 'C:\Program Files\GLPI-Agent\glpi-agent-core.bat')

if ($instalado) {
    Write-Log 'Ja estava instalado. Nenhuma acao necessaria.'
    exit 0
}

Write-Log 'Agente nao encontrado. Iniciando instalacao silenciosa...'

$ArgumentList = "/i `"$Msi`" /quiet /norestart SERVER=`"$ServerUrl`" RUNNOW=1 ADD_FIREWALL_EXCEPTION=1"
$processo = Start-Process -FilePath 'msiexec.exe' -ArgumentList $ArgumentList -Wait -NoNewWindow -PassThru

if ($processo.ExitCode -eq 0 -or $processo.ExitCode -eq 3010) {
    Write-Log 'Instalacao concluida.'
    exit 0
}

Write-Log "Falha na instalacao. Codigo msiexec $($processo.ExitCode)."
exit $processo.ExitCode
