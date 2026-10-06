const { exec } = require('child_process');
const path = require('path');

const msiPath = path.join(__dirname, 'GLPI-Agent-1.20-x64.msi');
const serverUrl = 'http://flowagente.floripa.sc.gov.br:8000/inventory';

// Comando para rodar a instalação com as propriedades já injetadas
const command = `msiexec.exe /i "${msiPath}" SERVER="${serverUrl}" RUNNOW=1 ADD_FIREWALL_EXCEPTION=1`;

console.log('Executando instalador customizado...');
exec(command, (error, stdout, stderr) => {
    if (error) {
        console.error(`Erro na instalação: ${error.message}`);
        return;
    }
    console.log('Instalação concluída com sucesso!');
});