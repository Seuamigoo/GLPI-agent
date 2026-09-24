import os
import xml.etree.ElementTree as ET
import zlib
import json
import time
from fastapi import FastAPI, Request, Response, BackgroundTasks
import uvicorn

app = FastAPI()

# Diretório para receber os milhares de ficheiros isolados sem conflitos
PASTA_RAW = "inventarios_brutos"
os.makedirs(PASTA_RAW, exist_ok=True)

def extrair_e_salvar_json(raw_body: bytes):
    """Tarefa executada em segundo plano para não bloquear a API."""
    try:
        try:
            xml_data = zlib.decompress(raw_body)
        except zlib.error:
            xml_data = raw_body 
            
        root = ET.fromstring(xml_data)
        content = root.find("CONTENT")
        
        if content is not None:
            hardware = content.find("HARDWARE")
            device_name = hardware.findtext("NAME", f"Desconhecido_{int(time.time())}") if hardware is not None else f"Desconhecido_{int(time.time())}"
            
            inventario_json = {"maquina": device_name, "timestamp_coleta": int(time.time())}
            
            # Extrai hardware geral
            if hardware is not None:
                inventario_json["hardware_geral"] = {
                    child.tag.lower(): child.text.strip() 
                    for child in hardware if child.text and child.text.strip()
                }

            # Extrai categorias e listas
            categorias = ["SOFTWARES", "CPUS", "MEMORIES", "STORAGES", "DRIVES", "NETWORKS", "VIDEOS", "BIOS", "CONTROLLERS"]
            for categoria in categorias:
                nodes = content.findall(categoria)
                if nodes:
                    inventario_json[categoria.lower()] = [
                        {child.tag.lower(): child.text.strip() for child in node if child.text and child.text.strip()}
                        for node in nodes
                    ]
            
            # Gravação segura: substitui apenas o JSON específico da máquina
            nome_json = os.path.join(PASTA_RAW, f"{device_name}.json")
            with open(nome_json, "w", encoding="utf-8") as f:
                json.dump(inventario_json, f, indent=4, ensure_ascii=False)
                
    except Exception as e:
        print(f"Erro ao processar inventário em background: {e}")

@app.post("/inventory")
async def receive_inventory(request: Request, background_tasks: BackgroundTasks):
    raw_body = await request.body()
    
    # Adiciona o trabalho pesado à fila do background
    background_tasks.add_task(extrair_e_salvar_json, raw_body)
    
    # Responde à máquina imediatamente em milissegundos
    return Response(content="<REPLY><RESPONSE>LOGGED</RESPONSE></REPLY>", media_type="application/xml")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)