import requests

def connect_to_polar():
    response = requests.get("http://localhost:8000/connect")
    if response.status_code == 200:
        print("Connected to Polar device")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def start_notifications():
    response = requests.get("http://localhost:8000/start_notifications")
    if response.status_code == 200:
        print("Notifications started")
    else:
        print(f"Error: {response.status_code} - {response.text}")


connect_to_polar()
start_notifications()

