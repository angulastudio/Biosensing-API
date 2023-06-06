import requests
import time

base_url = "http://localhost:8000"

def connect_to_polar():
    response = requests.get(f"{base_url}/connect")
    if response.status_code == 200:
        print("Conexión exitosa a Polar")
    else:
        print("Error al conectar a Polar")

def start_notifications():
    response = requests.get(f"{base_url}/start_notifications")
    if response.status_code == 200:
        print("Notificaciones iniciadas")
    else:
        print("Error al iniciar las notificaciones")

def get_heart_rate():
    response = requests.get(f"{base_url}/heart_rate")
    if response.status_code == 200:
        data = response.json()
        heart_rate = data["heart_rate"]
        print(f"Último valor del latido del corazón: {heart_rate}")
    else:
        print("Error al obtener el último valor del latido del corazón")

# Conectar a Polar y empezar las notificaciones
connect_to_polar()
start_notifications()

# Ejecutar la solicitud cada 10 segundos
while True:
    get_heart_rate()
    time.sleep(10)