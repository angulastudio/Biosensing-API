from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import PlainTextResponse
from bleak import BleakScanner, BleakClient
import asyncio
import struct
import math

app = FastAPI()

class PolarH10:
    # Códigos UUID de los servicios y características de Polar H10
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

def calculate_hrv(rr_intervals):
    if len(rr_intervals) < 2:
        return None

    differences = [rr_intervals[i] - rr_intervals[i-1] for i in range(1, len(rr_intervals))]
    squared_differences = [diff ** 2 for diff in differences]
    mean_squared_diff = sum(squared_differences) / len(squared_differences)
    rmssd = math.sqrt(mean_squared_diff)

    return rmssd

async def rr_peaks_handler(data):
    flags = struct.unpack('<B', data[0:1])[0]
    rr_interval_present = (flags >> 4) & 0x01
    if rr_interval_present:
        rr_interval1 = struct.unpack('<H', data[2:4])[0]
        rr_peaks_data.append(rr_interval1)
        if len(rr_peaks_data) >= 2:
            hrv_value = calculate_hrv(rr_peaks_data)
            if hrv_value is not None:
                hrv_data.append({
                    "rmssd": hrv_value
                })

hrv_range_min = 0
hrv_range_max = 100

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
        devices = await BleakScanner.discover()
        polar_devices = [device for device in devices if device.name is not None and "Polar" in device.name]
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
            hrv_value = round(hrv_data[-1]["rmssd"], 2)
            hrv_value = max(0, min(hrv_value, 100))
            return {"hrv": int(hrv_value)}

        raise HTTPException(status_code=404, detail="No HRV data available")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
