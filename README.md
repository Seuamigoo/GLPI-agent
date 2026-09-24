RECEPTOR GLPI-AGENT

Esse programa tem como objetivo receber as informações que estão sendo enviadas pelo GLPI Agent.

Utilização:

1) Execute o programa api_json.py.

2) Faça com que o agente aponte para http://IP_DO_API_JSON.PY:8000/inventory

3) Para cada máquina que se comunicar será gerado um .json com o nome da máquina e todas as suas informações serão salvas na pasta inventarios_brutos em formato json.
