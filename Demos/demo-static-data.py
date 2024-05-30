import requests
import time

base_url = "http://localhost:8000"

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


get_heart_rate()
get_rr_peaks()
get_hrv()