import requests
import time

base_url = "http://localhost:8000"


def set_address(address):
    response = requests.post(f"{base_url}/set_address", json={"address": address})
    if response.status_code == 200:
        print("Address set successfully")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def connect_to_polar():
    response = requests.get(f"{base_url}/connect")
    if response.status_code == 200:
        print("Connected to Polar device")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def start_notifications():
    response = requests.get(f"{base_url}/start_notifications")
    if response.status_code == 200:
        print("Notifications started")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def get_heart_rate():
    response = requests.get(f"{base_url}/heart_rate")
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
    response = requests.get(f"{base_url}/rr_peaks")
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
    response = requests.get(f"{base_url}/hrv")
    if response.status_code == 200:
        data = response.json()
        hrv = data.get("hrv")
        if hrv is not None:
            print(f"HRV: {hrv}")
        else:
            print("HRV data not available")
    else:
        print(f"Error: {response.status_code} - {response.text}")

# Set the device address
device_address = "D12EA708-D2E2-A337-3E1B-C75976067C2F"
set_address(device_address)

# Connect to Polar and start notifications
connect_to_polar()
start_notifications()

while True:
    get_heart_rate()
    get_rr_peaks()
    get_hrv()
    time.sleep(2)