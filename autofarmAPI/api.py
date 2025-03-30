from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
import os
import json
from datetime import datetime

app = FastAPI()

# Directorio de configuración
CONFIG_PATH = "./configs"
os.makedirs(CONFIG_PATH, exist_ok=True)

# Directorio para almacenar estados del cliente
STATE_PATH = "./states"
os.makedirs(STATE_PATH, exist_ok=True)

class UserConfig(BaseModel):
    commands: list
    interval: str
    prefix: str
    start_key: str
    collect: bool
    webhook_url: str

# Modelo para el estado del cliente
class ClientState(BaseModel):
    username: str
    activo: bool
    ultimo_comando: str
    saldo: str
    tipo_llave: str
    timestamp: datetime

# --- Endpoints de Configuración ---

@app.get("/config/{username}")
async def get_user_config(username: str):
    config_file_path = os.path.join(CONFIG_PATH, f"{username}.json")
    if not os.path.exists(config_file_path):
        raise HTTPException(status_code=404, detail="Config not found")
    
    with open(config_file_path, "r") as f:
        config_data = json.load(f)
    
    return config_data

@app.post("/config/{username}")
async def update_user_config(username: str, config: UserConfig):
    config_file_path = os.path.join(CONFIG_PATH, f"{username}.json")
    
    with open(config_file_path, "w") as f:
        json.dump(config.dict(), f, indent=4)
    
    return {"message": "Config updated successfully"}

@app.post("/config/{username}/upload")
async def upload_user_config(username: str, file: UploadFile = File(...)):
    config_file_path = os.path.join(CONFIG_PATH, f"{username}.json")
    
    with open(config_file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {"message": "Config file uploaded successfully"}

# --- Endpoints para el Estado del Cliente ---

@app.post("/estado/{username}")
async def update_client_state(username: str, state: ClientState):
    """
    Actualiza el estado del cliente para el usuario dado.
    """
    # Puedes almacenar el estado en un archivo JSON individual
    state_file_path = os.path.join(STATE_PATH, f"{username}.json")
    with open(state_file_path, "w") as f:
        json.dump(state.dict(), f, indent=4, default=str)
    return {"message": "Estado actualizado correctamente"}

@app.get("/estado/{username}")
async def get_client_state(username: str):
    """
    Obtiene el estado del cliente para el usuario dado.
    """
    state_file_path = os.path.join(STATE_PATH, f"{username}.json")
    if not os.path.exists(state_file_path):
        raise HTTPException(status_code=404, detail="Estado no encontrado")
    with open(state_file_path, "r") as f:
        state_data = json.load(f)
    return state_data
