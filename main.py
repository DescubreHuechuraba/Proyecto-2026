import math
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client

# Configura tus credenciales de Supabase
URL = "TU_URL_DE_SUPABASE"
KEY = "TU_API_KEY_DE_SUPABASE"
supabase: Client = create_client(URL, KEY)

app = FastAPI()

class Escaneo(BaseModel):
    user_id: str
    qr_id: str
    lat: float
    lon: float

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Radio de la Tierra en metros
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

@app.post("/validar")
async def validar_escaneo(data: Escaneo):
    # 1. Buscar el punto en la DB
    punto = supabase.table("puntos").select("*").eq("id", data.qr_id).single().execute()
    
    if not punto.data:
        raise HTTPException(status_code=404, detail="Punto no encontrado")

    # 2. Validar distancia (máximo 50 metros)
    distancia = haversine(data.lat, data.lon, punto.data['lat'], punto.data['lon'])
    
    if distancia > 50:
        return {"status": "error", "mensaje": f"Demasiado lejos. Estás a {int(distancia)}m."}

    # 3. Guardar el descubrimiento
    supabase.table("descubrimientos").insert({
        "user_id": data.user_id,
        "punto_id": data.qr_id
    }).execute()

    return {
        "status": "success",
        "nombre": punto.data['nombre'],
        "premio": punto.data['recompensa_texto']
    }