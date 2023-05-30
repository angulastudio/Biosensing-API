from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse
from bleak import BleakScanner, BleakClient
from polar import PolarH10
import asyncio
import uvicorn
import struct
from pyhrv import time_domain
import math


app = FastAPI()


heart_rate_data = []
rr_peaks_data = []
hrv_data = []
polar_device = PolarH10()

async def heart_rate_handler(data):
    heart_rate = struct.unpack('<B', data[1:2])[0]
    heart_rate_data.append(heart_rate)
    

async def rr_peaks_handler(data):
    # rr_peaks = (data[0] << 8) + data[1]
    rr_peaks = struct.unpack('<H', data[0:2])[0]
    rr_peaks_data.append(rr_peaks)
    if len(rr_peaks_data) >= 2:
        await calculate_hrv(rr_peaks_data)

hrv_range_min = 0
hrv_range_max = 100

min_sdnn = float('inf')
max_sdnn = -float('inf')
min_rmssd = float('inf')
max_rmssd = -float('inf')

async def calculate_hrv(rr_intervals):
    global min_sdnn, max_sdnn, min_rmssd, max_rmssd

    if len(rr_intervals) < 2:
        return

    # Calculate HRV measures
    sdnn = time_domain.sdnn(rr_intervals)[0]
    rmssd = time_domain.rmssd(rr_intervals)[0]

    # Handle NaN values
    if math.isnan(sdnn) or math.isnan(rmssd):
        return

    # Update min/max values
    min_sdnn = min(min_sdnn, sdnn)
    max_sdnn = max(max_sdnn, sdnn)
    min_rmssd = min(min_rmssd, rmssd)
    max_rmssd = max(max_rmssd, rmssd)

    # Normalize HRV measures
    normalized_sdnn = scale_to_range(sdnn, min_sdnn, max_sdnn, hrv_range_min, hrv_range_max)
    normalized_rmssd = scale_to_range(rmssd, min_rmssd, max_rmssd, hrv_range_min, hrv_range_max)

    # Append HRV data
    hrv_data.append({
        "sdnn": normalized_sdnn,
        "rmssd": normalized_rmssd
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

@app.get("/connect", responses={
    200: {"description": "Item retrieved successfully"},
    404: {"description": "Item not found"},
    500: {"description": "Item not found"}
})
async def connect_to_polar():
    """
    Connects to a Polar device (Polar H7, H9, and H10 devices are recommended). 
    The endpoint searches for a device with the name "Polar" and connects automatically.
    """
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

@app.get("/hrv")
async def stream_hrv():
    if polar_device.notifications_started:
        return StreamingResponse(generate_data(hrv_data), media_type="text/event-stream")
    else:
        raise HTTPException(status_code=404, detail="HRV notifications not started")

async def generate_data(data):
    while True:
        await asyncio.sleep(1)
        if data:
            value = data.pop()
            yield f"data: {value}\n\n"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
