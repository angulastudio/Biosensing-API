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
    response = requests.get("http://localhost:8000/heart_rate")
    if response.status_code == 200:
        data = response.json()
        heart_rate = data.get("heart_rate")
        if heart_rate is not None:
            print(f"Heart Rate: {heart_rate}")
        else:
            print("Heart rate data not available")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def get_rr_peaks():
    response = requests.get("http://localhost:8000/rr_peaks")
    if response.status_code == 200:
        data = response.json()
        rr_peaks = data.get("rr_peaks")
        if rr_peaks is not None:
            print(f"RR Peaks: {rr_peaks}")
        else:
            print("RR peaks data not available")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def get_hrv():
    response = requests.get("http://localhost:8000/hrv")
    if response.status_code == 200:
        data = response.json()
        # print("HRV data:", data)
        hrv = data.get("hrv")
        if hrv is not None:
            print(f"HRV: {hrv}")
        else:
            print("HRV data not available")
    else:
        print(f"Error: {response.status_code} - {response.text}")

# Conectar a Polar y empezar las notificaciones
connect_to_polar()
start_notifications()

# Ejecutar la solicitud cada 10 segundos
while True:
    get_heart_rate()
    get_rr_peaks()
    get_hrv()
    time.sleep(2)