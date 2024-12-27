import json
import os
import time
from dotenv import load_dotenv
import httpx

load_dotenv()

CLIENT_SECRET = os.getenv("CLIENT_SECRET")
CLIENT_ID = os.getenv("CLIENT_ID")

AUTH_TOKEN_URL = "https://api.mercadolibre.com/oauth/token"
TOKEN_FILE = "token_data.json"

# Función para cargar el token desde el archivo JSON
def load_token():
    try:
        with open(TOKEN_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

# Función para guardar el token en el archivo JSON
def save_token(data):
    with open(TOKEN_FILE, "w") as file:
        json.dump(data, file)

# Función para renovar el token si ha expirado
async def get_valid_token():
    token_data = load_token()
    current_time = int(time.time())  # Tiempo actual en segundos

    # Si el token no existe o ya expiró
    if not token_data or current_time >= token_data["expires_at"]:
        print("Token expirado. Solicitando uno nuevo...")

        # Parámetros de renovación del token
        client_id = CLIENT_ID
        client_secret = CLIENT_SECRET
        refresh_token = token_data["refresh_token"] if token_data else "YOUR_REFRESH_TOKEN"

        url = AUTH_TOKEN_URL
        payload = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=payload)

        if response.status_code == 200:
            new_token_data = response.json()
            # Calcular el tiempo de expiración (tiempo actual + expires_in)
            expires_at = current_time + new_token_data["expires_in"]

            # Guardar el nuevo token
            updated_token_data = {
                "access_token": new_token_data["access_token"],
                "refresh_token": new_token_data["refresh_token"],
                "expires_at": expires_at
            }
            save_token(updated_token_data)
            print("Nuevo token guardado.")
            return updated_token_data["access_token"]
        else:
            raise Exception(f"Error al renovar el token: {response.text}")
    else:
        print("Token válido. Reutilizando...")
        return token_data["access_token"]
