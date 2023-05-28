import asyncio
from datetime import datetime
from quart import Quart, jsonify, request, current_app
from bleak import BleakScanner, BleakClient
import threading

app = Quart(__name__)

class PolarH10:
    # Resto del código de la clase PolarH10 sin cambios
    ## DEVICE INFORMATION SERVICE
    DEVICE_INFORMATION_SERVICE = "0000180a-0000-1000-8000-00805f9b34fb"
    MANUFACTURER_NAME_UUID = "00002a29-0000-1000-8000-00805f9b34fb"
    MODEL_NBR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
    SERIAL_NUMBER_UUID = "00002a25-0000-1000-8000-00805f9b34fb"
    HARDWARE_REVISION_UUID = "00002a27-0000-1000-8000-00805f9b34fb"
    FIRMWARE_REVISION_UUID = "00002a26-0000-1000-8000-00805f9b34fb"
    SOFTWARE_REVISION_UUID = "00002a28-0000-1000-8000-00805f9b34fb"
    SYSTEM_ID_UUID = "00002a23-0000-1000-8000-00805f9b34fb"

    ## BATERY SERIVCE
    BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb"
    BATTERY_LEVEL_UUID = "00002a19-0000-1000-8000-00805f9b34fb"

    # Heart rate service
    HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
    HEART_RATE_CHARACTERISTIC_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

    def __init__(self, bleak_device):
        self.bleak_device = bleak_device
        self.bleak_client = BleakClient(self.bleak_device)

    async def connect(self):
        await self.bleak_client.connect()

    async def get_device_info(self):
        self.model_number = await self.bleak_client.read_gatt_char(PolarH10.MODEL_NBR_UUID)
        self.manufacturer_name = await self.bleak_client.read_gatt_char(PolarH10.MANUFACTURER_NAME_UUID)
        self.serial_number = await self.bleak_client.read_gatt_char(PolarH10.SERIAL_NUMBER_UUID)
        self.battery_level = await self.bleak_client.read_gatt_char(PolarH10.BATTERY_LEVEL_UUID)
        self.firmware_revision = await self.bleak_client.read_gatt_char(PolarH10.FIRMWARE_REVISION_UUID)
        self.hardware_revision = await self.bleak_client.read_gatt_char(PolarH10.HARDWARE_REVISION_UUID)
        self.software_revision = await self.bleak_client.read_gatt_char(PolarH10.SOFTWARE_REVISION_UUID)
    
    async def print_device_info(self):
        BLUE = "\033[94m"
        RESET = "\033[0m"
        print(f"Model Number: {BLUE}{''.join(map(chr, self.model_number))}{RESET}\n"
              f"Manufacturer Name: {BLUE}{''.join(map(chr, self.manufacturer_name))}{RESET}\n"
              f"Serial Number: {BLUE}{''.join(map(chr, self.serial_number))}{RESET}\n"
              f"Address: {BLUE}{self.bleak_device.address}{RESET}\n"
              f"Battery Level: {BLUE}{int(self.battery_level[0])}%{RESET}\n"
              f"Firmware Revision: {BLUE}{''.join(map(chr, self.firmware_revision))}{RESET}\n"
              f"Hardware Revision: {BLUE}{''.join(map(chr, self.hardware_revision))}{RESET}\n"
              f"Software Revision: {BLUE}{''.join(map(chr, self.software_revision))}{RESET}")

connected = False
heart_rate_queue = asyncio.Queue()

async def connect_to_polar():
    devices = await BleakScanner.discover()
    polar_device_found = False

    global polar_device

    for device in devices:
        if device.name is not None and "Polar" in device.name:
            polar_device_found = True
            polar_device = PolarH10(device)
            await polar_device.connect()
            await polar_device.get_device_info()
            await polar_device.print_device_info()

            async with BleakClient(device) as client:
                heart_rate_characteristic_uuid = "00002a37-0000-1000-8000-00805f9b34fb"
                await client.start_notify(heart_rate_characteristic_uuid, heart_rate_handler)

    if not polar_device_found:
        print("No Polar device found")

async def heart_rate_handler(sender, data):
    heart_rate = data[1]
    await heart_rate_queue.put(heart_rate)

def run_bleak_in_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(connect_to_polar())

def run_app():
    threading.Thread(target=run_bleak_in_thread, daemon=True).start()
    app.run()

@app.route('/connect', methods=['GET'])
async def connect():
    global connected
    if connected:
        return jsonify({'message': 'Already connected to PolarH10'})

    connected = True
    return jsonify({'message': 'Connecting to PolarH10'})

@app.route('/heart-rate')
async def get_heart_rate():
    async def stream():
        while True:
            heart_rate = await heart_rate_queue.get()
            yield f"data: {heart_rate}\n\n"

    return app.response_class(stream(), mimetype='text/event-stream')

if __name__ == '__main__':
    run_app()