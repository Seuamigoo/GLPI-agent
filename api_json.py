import os
import re
import xml.etree.ElementTree as ET
import zlib
import json
import time
import urllib.error
import urllib.request
from fastapi import FastAPI, Request, Response, BackgroundTasks
import uvicorn

app = FastAPI()

# Diretório para receber os milhares de ficheiros isolados sem conflitos
PASTA_RAW = "inventarios_brutos"
os.makedirs(PASTA_RAW, exist_ok=True)

# Servidor que recebe o inventário já convertido em JSON
SERVIDOR_DESTINO = "https://flowagente.floripa.sc.gov.br"
URL_ENVIO_INVENTARIO = f"{SERVIDOR_DESTINO}/inventory"

# PROLOG_FREQ é em horas: o agente volta a contactar depois deste intervalo
PROLOG_FREQ_HORAS = 12

RESPOSTA_PROLOG = (
    "<REPLY><RESPONSE>SEND</RESPONSE>"
    f"<PROLOG_FREQ>{PROLOG_FREQ_HORAS}</PROLOG_FREQ></REPLY>"
)
RESPOSTA_INVENTARIO = "<REPLY><RESPONSE>LOGGED</RESPONSE></REPLY>"

CATEGORIAS = (
    "cpus",
    "memories",
    "storages",
    "drives",
    "networks",
    "videos",
    "bios",
    "controllers",
    "softwares",
)
CARACTERES_INVALIDOS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def decodificar_corpo(raw_body: bytes) -> bytes:
    try:
        return zlib.decompress(raw_body)
    except zlib.error:
        return raw_body


def sanitizar_nome(valor: str) -> str:
    return CARACTERES_INVALIDOS.sub("", valor).strip().strip(".")


def caminho_inventario(hostname: str, uuid: str) -> str:
    """Um arquivo por máquina. Reenvio da mesma máquina só substitui o dela."""
    host = sanitizar_nome(hostname) or f"Desconhecido_{int(time.time())}"
    uid = sanitizar_nome(uuid)
    nome = f"{host}__{uid}.json" if uid else f"{host}.json"
    return os.path.join(PASTA_RAW, nome)


def montar_inventario(content: ET.Element) -> dict:
    hardware = content.find("HARDWARE")
    hardware_geral = {}
    if hardware is not None:
        hardware_geral = {
            child.tag.lower(): child.text.strip()
            for child in hardware
            if child.text and child.text.strip()
        }
    hardware_geral.pop("winprodkey", None)

    device_name = hardware_geral.get("name") or f"Desconhecido_{int(time.time())}"
    inventario = {
        "maquina": device_name,
        "uuid": hardware_geral.get("uuid", ""),
        "timestamp_coleta": int(time.time()),
        "hardware_geral": hardware_geral,
    }
    for categoria in CATEGORIAS:
        nodes = content.findall(categoria.upper())
        inventario[categoria] = [
            {
                child.tag.lower(): child.text.strip()
                for child in node
                if child.text and child.text.strip()
            }
            for node in nodes
        ]
    return inventario


def extrair_e_salvar_json(xml_data: bytes):
    """Grava o JSON da máquina e repassa o mesmo conteúdo. Falha de envio não apaga o arquivo."""
    try:
        root = ET.fromstring(xml_data)
        content = root.find("CONTENT")
        if content is None:
            return

        inventario_json = montar_inventario(content)
        nome_json = caminho_inventario(inventario_json["maquina"], inventario_json["uuid"])
        with open(nome_json, "w", encoding="utf-8") as f:
            json.dump(inventario_json, f, indent=4, ensure_ascii=False)

        enviar_inventario(inventario_json)
    except Exception as e:
        print(f"Erro ao processar inventário em background: {e}")


def enviar_inventario(inventario_json: dict):
    """Envia o JSON do inventário ao servidor central. Falha de rede não apaga o arquivo local."""
    token = os.environ.get("FLOWAGENTE_API_KEY", "").strip()
    if not token:
        print(
            "FLOWAGENTE_API_KEY ausente. Inventário de "
            f"{inventario_json.get('maquina')} gravado localmente e não enviado."
        )
        return

    payload = json.dumps(inventario_json, ensure_ascii=False).encode("utf-8")
    requisicao = urllib.request.Request(
        URL_ENVIO_INVENTARIO,
        data=payload,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "X-API-Key": token,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=30) as resposta:
            resposta.read()
        print(
            f"Inventário de {inventario_json.get('maquina')} enviado para "
            f"{URL_ENVIO_INVENTARIO} (HTTP {resposta.status})"
        )
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"Falha ao enviar inventário para {URL_ENVIO_INVENTARIO}: {e}")


@app.post("/inventory")
async def receive_inventory(request: Request, background_tasks: BackgroundTasks):
    raw_body = await request.body()
    try:
        xml_data = decodificar_corpo(raw_body)
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"XML inválido, inventário ignorado: {e}")
        return Response(content=RESPOSTA_INVENTARIO, media_type="application/xml")

    # PROLOG: contato sem CONTENT. Não grava e não repassa.
    if root.find("CONTENT") is None:
        return Response(content=RESPOSTA_PROLOG, media_type="application/xml")

    background_tasks.add_task(extrair_e_salvar_json, xml_data)
    return Response(content=RESPOSTA_INVENTARIO, media_type="application/xml")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
