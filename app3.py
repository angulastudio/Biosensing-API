from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse
from bleak import BleakScanner, BleakClient
import asyncio
import uvicorn
import struct

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
polar_device = PolarH10()

async def heart_rate_handler(data):
    heart_rate = struct.unpack('<B', data[1:2])[0]
    heart_rate_data.append(heart_rate)

async def rr_peaks_handler(data):
    rr_peaks = struct.unpack('<H', data[0:2])[0]
    rr_peaks_data.append(rr_peaks)

async def scan_polar_devices():
    devices = await BleakScanner.discover()
    polar_devices = []
    for device in devices:
        if device.name is not None and "Polar" in device.name:
            polar_devices.append(device)
    return polar_devices

@app.on_event("startup")
async def startup_event():
    try:
        polar_devices = await scan_polar_devices()
        if not polar_devices:
            print("No Polar devices found")
            return

        await polar_device.connect(polar_devices[0])
        print("Connected to Polar device")

    except Exception as e:
        print(str(e))

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
    if not polar_device.notifications_started:
        polar_device.subscribers.append(heart_rate_handler)
        polar_device.subscribers.append(rr_peaks_handler)
        await polar_device.start_notifications()
        return {"message": "Notifications started"}
    else:
        return {"message": "Notifications already started"}

@app.get("/stop_notifications")
async def stop_notifications():
    if polar_device.notifications_started:
        polar_device.subscribers.remove(heart_rate_handler)
        polar_device.subscribers.remove(rr_peaks_handler)
        await polar_device.stop_notifications()
        return {"message": "Notifications stopped"}
    else:
        return {"message": "Notifications not started"}

@app.get("/heart_rate")
async def stream_heart_rate():
    if polar_device.notifications_started:
        return StreamingResponse(generate_data(heart_rate_data), media_type="text/event-stream")
    else:
        raise HTTPException(status_code=404, detail="Heart rate notifications not started")

@app.get("/rr_peaks")
async def stream_rr_peaks():
    if polar_device.notifications_started:
        return StreamingResponse(generate_data(rr_peaks_data), media_type="text/event-stream")
    else:
        raise HTTPException(status_code=404, detail="RR peaks notifications not started")

async def generate_data(data):
    while True:
        await asyncio.sleep(1)
        if data:
            value = data.pop()
            yield f"data: {value}\n\n"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
