from fastapi import FastAPI
from starlette.responses import StreamingResponse
from bleak import BleakScanner, BleakClient
from datetime import datetime
import asyncio

app = FastAPI()

class PolarH10:
    HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
    HEART_RATE_CHARACTERISTIC_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

    def __init__(self):
        self.bleak_device = None
        self.bleak_client = None

    async def connect(self, device):
        self.bleak_device = device
        self.bleak_client = BleakClient(self.bleak_device)
        await self.bleak_client.connect()

    async def disconnect(self):
        if self.bleak_client:
            await self.bleak_client.disconnect()

    async def start_heart_rate_notifications(self, callback):
        await self.bleak_client.start_notify(
            PolarH10.HEART_RATE_CHARACTERISTIC_UUID,
            callback
        )

    async def stop_heart_rate_notifications(self):
        await self.bleak_client.stop_notify(
            PolarH10.HEART_RATE_CHARACTERISTIC_UUID
        )

    async def get_heart_rate(self):
        value = await self.bleak_client.read_gatt_char(
            PolarH10.HEART_RATE_CHARACTERISTIC_UUID
        )
        heart_rate = value[1]
        return heart_rate

heart_rate_data = []
polar_device = PolarH10()

async def heart_rate_handler(sender, data):
    heart_rate = data[1]
    heart_rate_data.append(heart_rate)
    timestamp = datetime.now().strftime('%H:%M:%S.%f')
    print("Heart Rate:", heart_rate, timestamp)

async def scan_polar_devices():
    devices = await BleakScanner.discover()
    polar_devices = []
    for device in devices:
        if device.name is not None and "Polar" in device.name:
            polar_devices.append(device)
    return polar_devices

@app.get("/connect")
async def connect_to_polar():
    try:
        polar_devices = await scan_polar_devices()
        if not polar_devices:
            return {"message": "No Polar devices found"}

        await polar_device.connect(polar_devices[0])
        return {"message": "Connected to Polar device"}

    except Exception as e:
        return {"message": str(e)}

@app.get("/heart_rate")
async def stream_heart_rate():
    async def generate_heart_rate():
        try:
            await polar_device.start_heart_rate_notifications(heart_rate_handler)

            while True:
                await asyncio.sleep(1)
                if heart_rate_data:
                    heart_rate = heart_rate_data.pop()
                    yield f"data: {heart_rate}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n"

        finally:
            await polar_device.stop_heart_rate_notifications()

    return StreamingResponse(generate_heart_rate(), media_type="text/event-stream")

@app.on_event("shutdown")
async def shutdown_event():
    await polar_device.disconnect()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
