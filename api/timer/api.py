from fastapi import FastAPI, Request
import httpx
from datetime import datetime
import pytz
import logging
import json

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IPINFO_TOKEN = "493a61ee8ee052"

async def get_user_timezone(ip_address: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://ipinfo.io/{ip_address}/json?token={IPINFO_TOKEN}")
            response.raise_for_status()
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Error al decodificar JSON de IPinfo: {e}, response: {response.text}")
                return None
            timezone_str = data.get("timezone")
            if timezone_str:
                return pytz.timezone(timezone_str)
            else:
                logger.warning(f"No se encontró la zona horaria en la respuesta de IPinfo para IP: {ip_address}")
                return None
    except httpx.HTTPStatusError as e:
        logger.error(f"Error HTTP al obtener la zona horaria: {e}, status: {e.response.status_code}, content: {e.response.text}")
        return None
    except httpx.RequestError as e:
        logger.error(f"Error de solicitud al obtener la zona horaria: {e}")
        return None
    except pytz.exceptions.UnknownTimeZoneError as e:
        logger.error(f"Zona horaria desconocida: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado al obtener la zona horaria: {e}")
        return None

async def get_client_ip(request: Request):
    if "x-forwarded-for" in request.headers:
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    if "x-real-ip" in request.headers:
        return request.headers["x-real-ip"].strip()
    return request.client.host

def get_greeting(current_hour: int):
    if 6 <= current_hour < 12:
        return "Buenos días, Usuario"
    elif 12 <= current_hour < 20:
        return "Buenas tardes, Usuario"
    else:
        return "Buenas noches, Usuario"

@app.get("/greeting")
async def read_greeting(request: Request):
    client_host = await get_client_ip(request) # Espera el resultado de la corrutina
    timezone = await get_user_timezone(client_host)

    if timezone:
        current_time = datetime.now(timezone)
        greeting = get_greeting(current_time.hour)
        return {"greeting": greeting, "timezone": str(timezone)}
    else:
        return {"greeting": "Hola, Usuario", "message": "No se pudo determinar la zona horaria."}

@app.get("/time")
async def read_time(request: Request):
    client_host = await get_client_ip(request) # Espera el resultado de la corrutina
    timezone = await get_user_timezone(client_host)

    if timezone:
        current_time = datetime.now(timezone)
        return {"time": current_time.isoformat(), "timezone": str(timezone)}
    else:
        return {"error": "No se pudo determinar la zona horaria."}

@app.get("/test_ip")
async def test_ip(request: Request):
    client_ip = await get_client_ip(request) # Espera el resultado de la corrutina
    return {"client_ip": client_ip}