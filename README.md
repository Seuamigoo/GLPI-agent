RECEPTOR GLPI-AGENT

Esse programa tem como objetivo receber as informações que estão sendo enviadas pelo GLPI Agent.

Utilização:

1) Execute o programa api_json.py.

2) Faça com que o agente aponte para http://IP_DO_API_JSON.PY:8000/inventory

3) Para cada máquina que se comunicar será gerado um .json com o nome da máquina e o uuid na pasta inventarios_brutos.

4) Defina a variável de ambiente FLOWAGENTE_API_KEY com o token do servidor central. Cada inventário é reenviado por POST para https://flowagente.floripa.sc.gov.br/inventory, com os cabeçalhos Content-Type: application/json; charset=utf-8 e X-API-Key. Sem essa variável o JSON fica só no disco.
