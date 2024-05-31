# Biosensing API

[![forthebadge](https://forthebadge.com/images/badges/made-with-python.svg)](https://forthebadge.com)
[![forthebadge](https://forthebadge.com/images/badges/powered-by-coffee.svg)](https://forthebadge.com)
[![forthebadge](https://forthebadge.com/images/badges/makes-people-smile.svg)](https://forthebadge.com)

## Table of Contents

1. [Description](#description)
2. [Installation](#installation)
3. [Base URL](#base-url)
4. [Endpoints](#endpoints)
    - [1. Set Device Address](#1-set-device-address)
    - [2. Connect to Polar Device](#2-connect-to-polar-device)
    - [3. Start Notifications](#3-start-notifications)
    - [4. Stop Notifications](#4-stop-notifications)
    - [5. Get Heart Rate](#5-get-heart-rate)
    - [6. Get RR Peaks](#6-get-rr-peaks)
    - [7. Get HRV](#7-get-hrv)
5. [Example Scripts](#example-scripts)
    - [First Script: Connect and Start Notifications](#first-script-connect-and-start-notifications)
    - [Second Script: Continuously Monitor Data](#second-script-continuously-monitor-data)
6. [Postman Collection](#postman-collection)



## Description
The Biosensing API is an API that streams real-time data from Polar heart rate sensors. It transmits real-time data such as heartbeats, RR peaks, and HRV.

## Installation

1. Clone the repository
```bash
   git clone git@github.com:ServirGt/Biosensing-API.git
```
2. Create an enviroment (optional but recommended)
```bash
   python3 -m venv venv
```

3. Activate the virtual environment
```bash
   source venv/bin/activate
```

4. Install requirements
```bash
   pip3 install -r requirements.txt
```

## Running the API
```bash
   uvicorn app:app --reload
```

## Base URL
http://localhost:8000

## Endpoints

### 1. Set Device Address

- **URL**: `/set_address`
- **Method**: `POST`
- **Description**: Sets the address of the Polar device.

#### Request Body

```json
{
    "address": "ADDRESS POLAR DEVICE"
}
```

#### Response
```json
{
    "message": "Device address set to D12EA708-D2E2-A337-3E1B-C75976067C2F"
}
```

#### Example usage
```sh
curl -X POST "http://localhost:8000/set_address" -H "Content-Type: application/json" -d '{"address": "ADDRESS POLAR DEVICE"}'
```


### 2. Connect to Polar Device

- **URL**: `/connect`
- **Method**: `GET`
- **Description**: Connects to the Polar device with the previously set address.

#### Response
```json
{
    "message": "Connected to Polar device"
}
```

#### Example usage
```sh
curl -X GET "http://localhost:8000/connect"
```

### 3. Start Notifications

- **URL**: `/start_notifications`
- **Method**: `GET`
- **Description**: Starts heart rate and RR notifications from the Polar device.

#### Response
```json
{
    "message": "Notifications started"
}
```

#### Example usage
```sh
curl -X GET "http://localhost:8000/start_notifications"
```

### 4. Stop Notifications

- **URL**: `/stop_notifications`
- **Method**: `GET`
- **Description**: Stops notifications and returns the final average HRV.

#### Response
```json
{
    "message": "Final average HRV: 85.23\nNotifications stopped"
}
```

#### Example usage
```sh
curl -X GET "http://localhost:8000/stop_notifications"
```

### 5. Get Heart Rate

- **URL**: `/heart_rate`
- **Method**: `GET`
- **Description**: Returns the latest heart rate reading.

#### Response
```json
{
    "heart_rate": 65
}
```

#### Example usage
```sh
curl -X GET "http://localhost:8000/heart_rate"
```

### 6. Get RR Peaks

- **URL**: `/rr_peaks`
- **Method**: `GET`
- **Description**: Returns the latest RR peaks reading.

#### Response
```json
{
    "rr_peaks": 1100
}
```

#### Example usage
```sh
curl -X GET "http://localhost:8000/rr_peaks"
```

### 7. Get HRV

- **URL**: `/hrv`
- **Method**: `GET`
- **Description**: Returns the average HRV of the last 10 readings.

#### Response
```json
{
    "hrv": 75.42
}
```

#### Example usage
```sh
curl -X GET "http://localhost:8000/hrv"
```


## Postman Collection

We have provided a Postman collection to help you test and interact with the PolarAPI.

### Importing the Collection

1. Download the [PolarAPI Postman Collection](./PolarAPI.postman_collection.json).
2. Open Postman and go to the "Collections" tab.
3. Click the "Import" button and select the downloaded JSON file.

### Setting Up Environment Variables

1. In Postman, go to the "Environments" tab.
2. Click the "Import" button and select the [PolarAPI Environment](./Biosense.postman_environment.json) file.
3. Ensure the `base_url` and `device_address` variables are correctly set in the environment.

### Using the Collection

1. Select the `Biosense` environment in Postman.
2. Use the requests in the `Biosense` collection to interact with the API.

#### Requests Available on the Collection

- **Scan**: Sets the address of the Polar device.
- **Set Address**: Sets the address of the Polar device.
- **Connect**: Connects to the Polar device.
- **Start Notifications**: Starts heart rate and RR notifications.
- **Stop Notifications**: Stops notifications and returns the final average HRV.
- **Heart Rate**: Returns the latest heart rate reading.
- **RR Peaks**: Returns the latest RR peaks reading.
- **HRV**: Returns the average HRV of the last 10 readings.


## License

Licensed under the MIT License, Copyright © 2023-present Servir