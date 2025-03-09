from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import shutil
from pathlib import Path
import pymysql

app = FastAPI()

# Datos de conexión a MySQL en Railway
DB_HOST = "gondola.proxy.rlwy.net"
DB_USER = "root"
DB_PASSWORD = "GXEBZnKBAXxMfJNjHeSoAcQgVPlCnseN"
DB_NAME = "railway"
DB_PORT = 52136

# Conectar con la base de datos MySQL
try:
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        ssl={"ssl": {}}
    )
    print("✅ Conexión exitosa a MySQL en Railway")
    cursor = conn.cursor()
except Exception as e:
    print(f"❌ Error de conexión a MySQL: {e}")

# Carpeta principal de almacenamiento
BASE_UPLOAD_FOLDER = Path("uploads")
BASE_UPLOAD_FOLDER.mkdir(exist_ok=True)

# Tamaño máximo de archivos (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

def get_safe_filename(filename: str) -> str:
    """Evita ataques de path traversal"""
    return os.path.basename(filename)

def get_user_folder(user_id: int) -> Path:
    """Devuelve la carpeta de almacenamiento del usuario"""
    user_folder = BASE_UPLOAD_FOLDER / str(user_id)
    user_folder.mkdir(exist_ok=True)  # Crea la carpeta si no existe
    return user_folder

def validate_user(user_id: int):
    """Verifica si el usuario existe en la base de datos"""
    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

@app.post("/upload/{user_id}/")
async def upload_file(user_id: int, file: UploadFile = File(...)):
    validate_user(user_id)

    # Verificar el tamaño
    file_size = file.file.seek(0, os.SEEK_END)
    file.file.seek(0)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande (máx. 10MB)")

    filename = get_safe_filename(file.filename)
    user_folder = get_user_folder(user_id)
    file_location = user_folder / filename

    # Evitar sobrescritura
    counter = 1
    while file_location.exists():
        file_location = user_folder / f"{filename.rsplit('.', 1)[0]}_{counter}.{filename.rsplit('.', 1)[-1]}"
        counter += 1

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": filename, "message": "Archivo subido con éxito"}

@app.get("/download/{user_id}/{filename}")
async def download_file(user_id: int, filename: str):
    validate_user(user_id)

    safe_filename = get_safe_filename(filename)
    file_path = get_user_folder(user_id) / safe_filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    return FileResponse(file_path, filename=safe_filename)

@app.delete("/delete/{user_id}/{filename}")
async def delete_file(user_id: int, filename: str):
    validate_user(user_id)

    safe_filename = get_safe_filename(filename)
    file_path = get_user_folder(user_id) / safe_filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    file_path.unlink()
    return {"message": "Archivo eliminado con éxito"}

@app.get("/list/{user_id}/")
async def list_files(user_id: int):
    validate_user(user_id)

    user_folder = get_user_folder(user_id)
    files = [f.name for f in user_folder.iterdir() if f.is_file()]
    
    return {"files": files}
