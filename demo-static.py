import requests
import time
import json

API_URL = "http://localhost:8000"

def connect_and_start_notifications():
    response = requests.get(f"{API_URL}/connect")
    if response.status_code == 200:
        print("Connected to Polar device")
    else:
        print("Failed to connect to Polar device")

    response = requests.get(f"{API_URL}/start_notifications")
    if response.status_code == 200:
        print("Notifications started")
    else:
        print("Failed to start notifications")

def get_latest_heart_rate():
    response = requests.get(f"{API_URL}/heart_rate")
    if response.status_code == 200:
        data = response.text.strip().split("\n")
        if data:
            json_data = json.loads(data[-1])
            heart_rate = json_data.get("heart_rate")
            if heart_rate is not None:
                return int(heart_rate)
    return None

def get_latest_rr_peaks():
    response = requests.get(f"{API_URL}/rr_peaks")
    if response.status_code == 200:
        data = response.text.strip().split("\n")
        if data:
            json_data = json.loads(data[-1])
            rr_peaks = json_data.get("rr_peaks")
            if rr_peaks is not None:
                return int(rr_peaks)
    return None

def get_latest_hrv():
    response = requests.get(f"{API_URL}/hrv")
    if response.status_code == 200:
        data = response.text.strip().split("\n")
        if data:
            json_data = json.loads(data[-1])
            hrv = json_data.get("hrv")
            if hrv is not None:
                rmssd = hrv.get("rmssd")
                if rmssd is not None:
                    return float(rmssd)
    return None

def print_latest_data():
    heart_rate = get_latest_heart_rate()
    rr_peaks = get_latest_rr_peaks()

    if heart_rate is not None:
        print(f"Heart Rate: {heart_rate} bpm")
    else:
        print("Heart Rate data not available")

    if rr_peaks is not None:
        print(f"RR Peaks: {rr_peaks} ms")
    else:
        print("RR Peaks data not available")

    # Esperar 10 segundos antes de obtener el valor de HRV
    time.sleep(5)

    hrv = get_latest_hrv()

    if hrv is not None:
        print(f"HRV (RMSSD): {hrv}")
    else:
        print("HRV data not available")


connect_and_start_notifications()
print_latest_data()
