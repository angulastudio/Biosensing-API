from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import PlainTextResponse
from bleak import BleakScanner, BleakClient
import asyncio
import uvicorn
import struct
from pyhrv import time_domain
import math


app = FastAPI()

class PolarH10:
    HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
    HEART_RATE_CHARACTERISTIC_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

    def __init__(self):
        self.bleak_device = None
        self.bleak_client = None
        self.subscribers = []
        self.notifications_started = False

    async def connect(self, device):
        self.bleak_device = device
        self.bleak_client = BleakClient(self.bleak_device)
        await self.bleak_client.connect()

    async def disconnect(self):
        if self.bleak_client:
            await self.bleak_client.disconnect()

    async def start_notifications(self):
        await self.bleak_client.start_notify(
            PolarH10.HEART_RATE_CHARACTERISTIC_UUID,
            self.notification_callback
        )
        self.notifications_started = True

    async def stop_notifications(self):
        await self.bleak_client.stop_notify(
            PolarH10.HEART_RATE_CHARACTERISTIC_UUID
        )
        self.notifications_started = False

    async def notify_subscribers(self, data):
        for subscriber in self.subscribers:
            await subscriber(data)

    async def notification_callback(self, sender, data):
        await self.notify_subscribers(data)

heart_rate_data = []
rr_peaks_data = []
hrv_data = []
polar_device = PolarH10()

async def heart_rate_handler(data):
    heart_rate = struct.unpack('<B', data[1:2])[0]
    heart_rate_data.append(heart_rate)

async def rr_peaks_handler(data):
    flags = struct.unpack('<B', data[0:1])[0]
    rr_interval_present = (flags >> 4) & 0x01
    if rr_interval_present:
        rr_interval1 = struct.unpack('<H', data[2:4])[0]
        rr_peaks_data.append(rr_interval1)
        if len(rr_peaks_data) >= 2:
            await calculate_hrv(rr_peaks_data)

hrv_range_min = 0
hrv_range_max = 100
min_rmssd = float('inf')
max_rmssd = -float('inf')

def normalize_hrv(value, value_min, value_max, range_min, range_max):
    if value_min == value_max:
        return range_min  # Evitar división por cero
    normalized_value = (math.log(value) - math.log(value_min)) / (math.log(value_max) - math.log(value_min)) * (range_max - range_min) + range_min
    normalized_value = min(max(normalized_value, range_min), range_max)
    return normalized_value


async def calculate_hrv(rr_intervals):
    # global min_sdnn, max_sdnn, min_rmssd, max_rmssd
    global min_rmssd, max_rmssd


    if len(rr_intervals) < 2:
        return

    # Calculate HRV measures
    # sdnn = time_domain.sdnn(rr_intervals)[0]
    rmssd = time_domain.rmssd(rr_intervals)[0]

    # Handle NaN values
    # if math.isnan(sdnn) or math.isnan(rmssd):
    if math.isnan(rmssd):
        return

    # Update min/max values
    # min_sdnn = min(min_sdnn, sdnn)
    # max_sdnn = max(max_sdnn, sdnn)
    min_rmssd = min(min_rmssd, rmssd)
    max_rmssd = max(max_rmssd, rmssd)

    # Normalize HRV measures
    # normalized_sdnn = normalize_hrv(sdnn, min_sdnn, max_sdnn, hrv_range_min, hrv_range_max)
    normalized_rmssd = normalize_hrv(rmssd, min_rmssd, max_rmssd, hrv_range_min, hrv_range_max)

    # Append HRV data
    hrv_data.append({
        # "sdnn": normalized_sdnn,
        "rmssd": rmssd
    })

def scale_to_range(value, value_min, value_max, range_min, range_max):
    scaled_value = ((value - value_min) / (value_max - value_min)) * (range_max - range_min) + range_min
    return scaled_value

async def scan_polar_devices():
    devices = await BleakScanner.discover()
    polar_devices = []
    for device in devices:
        if device.name is not None and "Polar" in device.name:
            polar_devices.append(device)
    return polar_devices

@app.on_event("shutdown")
async def shutdown_event():
    await polar_device.disconnect()

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )

@app.get("/connect")
async def connect_to_polar():
    try:
        polar_devices = await scan_polar_devices()
        if not polar_devices:
            raise HTTPException(status_code=404, detail="No Polar devices found")

        await polar_device.connect(polar_devices[0])
        return {"message": "Connected to Polar device"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/start_notifications")
async def start_notifications():
    try:
        if not polar_device.notifications_started:
            polar_device.subscribers.append(heart_rate_handler)
            polar_device.subscribers.append(rr_peaks_handler)
            await polar_device.start_notifications()
            return {"message": "Notifications started"}

        raise HTTPException(status_code=500, detail="Notifications already started")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stop_notifications")
async def stop_notifications():
    try:
        if polar_device.notifications_started:
            polar_device.subscribers.remove(heart_rate_handler)
            polar_device.subscribers.remove(rr_peaks_handler)
            await polar_device.stop_notifications()
            return {"message": "Notifications stopped"}

        raise HTTPException(status_code=500, detail="Notifications already stopped")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/heart_rate")
async def get_heart_rate():
    try:
        if heart_rate_data:
            return {"heart_rate": heart_rate_data[-1]}

        raise HTTPException(status_code=404, detail="No heart rate data available")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rr_peaks")
async def get_rr_peaks():
    try:
        if rr_peaks_data:
            return {"rr_peaks": rr_peaks_data[-1]}

        raise HTTPException(status_code=404, detail="No RR peaks data available")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/hrv")
async def get_hrv():
    try:
        if hrv_data:
            return {"hrv": hrv_data[-1]}

        raise HTTPException(status_code=404, detail="No HRV data available")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
