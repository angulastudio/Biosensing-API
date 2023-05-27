from bleak import BleakScanner, BleakClient
import asyncio
from datetime import datetime

class PolarH10:
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

    async def connect_device(self):
        self.bleak_client = BleakClient(self.bleak_device)
        await self.bleak_client.connect()


    async def get_device_info_(self):
        self.model_number = await self.bleak_client.read_gatt_char(PolarH10.MODEL_NBR_UUID)
        self.manufacturer_name = await self.bleak_client.read_gatt_char(PolarH10.MANUFACTURER_NAME_UUID)
        self.serial_number = await self.bleak_client.read_gatt_char(PolarH10.SERIAL_NUMBER_UUID)
        self.battery_level = await self.bleak_client.read_gatt_char(PolarH10.BATTERY_LEVEL_UUID)
        self.firmware_revision = await self.bleak_client.read_gatt_char(PolarH10.FIRMWARE_REVISION_UUID)
        self.hardware_revision = await self.bleak_client.read_gatt_char(PolarH10.HARDWARE_REVISION_UUID)
        self.software_revision = await self.bleak_client.read_gatt_char(PolarH10.SOFTWARE_REVISION_UUID)

    async def print_device_info(self):
        print(f"Model Number: {self.model_number}\n"
            f"Manufacturer Name: {self.manufacturer_name}\n"
            f"Serial Number: {self.serial_number}\n"
            f"Address: {self.bleak_device.address}\n"
            f"Battery Level: {self.battery_level}%\n"
            f"Firmware Revision: {self.firmware_revision}\n"
            f"Hardware Revision: {self.hardware_revision}\n"
            f"Software Revision: {self.software_revision}")
        
    async def read_heart_rate(self):
        heart_rate_data = await self.bleak_client.read_gatt_char(PolarH10.HEART_RATE_CHARACTERISTIC_UUID)
        heart_rate = heart_rate_data[1]
        print(heart_rate)
        return heart_rate
    
    async def stream_heart_rate2(self):
        while True:
            heart_rate_data = await self.bleak_client.read_gatt_char(PolarH10.HEART_RATE_CHARACTERISTIC_UUID)
            heart_rate = heart_rate_data[1]
            yield str(heart_rate)
            await asyncio.sleep(1)
