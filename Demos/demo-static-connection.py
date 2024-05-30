import requests

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

# Set the device address
device_address = "ADDRESS"
set_address(device_address)

# Connect to Polar and start notifications
connect_to_polar()
start_notifications()