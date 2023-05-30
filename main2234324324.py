# from bleak import BleakScanner, BleakClient
# import asyncio
# from datetime import datetime
# import time



# class PolarH10:
#     ## DEVICE INFORMATION SERVICE
#     DEVICE_INFORMATION_SERVICE = "0000180a-0000-1000-8000-00805f9b34fb"
#     MANUFACTURER_NAME_UUID = "00002a29-0000-1000-8000-00805f9b34fb"
#     MODEL_NBR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
#     SERIAL_NUMBER_UUID = "00002a25-0000-1000-8000-00805f9b34fb"
#     HARDWARE_REVISION_UUID = "00002a27-0000-1000-8000-00805f9b34fb"
#     FIRMWARE_REVISION_UUID = "00002a26-0000-1000-8000-00805f9b34fb"
#     SOFTWARE_REVISION_UUID = "00002a28-0000-1000-8000-00805f9b34fb"
#     SYSTEM_ID_UUID = "00002a23-0000-1000-8000-00805f9b34fb"

#     ## BATERY SERIVCE
#     BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb"
#     BATTERY_LEVEL_UUID = "00002a19-0000-1000-8000-00805f9b34fb"

#     # Heart rate service
#     HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
#     HEART_RATE_CHARACTERISTIC_UUID = "00002a37-0000-1000-8000-00805f9b34fb"



#     def __init__(self, bleak_device):
#         self.bleak_device = bleak_device


#     async def connect(self):
#         self.bleak_client = BleakClient(self.bleak_device)
#         await self.bleak_client.connect()

#     async def get_device_info(self):
#         self.model_number = await self.bleak_client.read_gatt_char(PolarH10.MODEL_NBR_UUID)
#         self.manufacturer_name = await self.bleak_client.read_gatt_char(PolarH10.MANUFACTURER_NAME_UUID)
#         self.serial_number = await self.bleak_client.read_gatt_char(PolarH10.SERIAL_NUMBER_UUID)
#         self.battery_level = await self.bleak_client.read_gatt_char(PolarH10.BATTERY_LEVEL_UUID)
#         self.firmware_revision = await self.bleak_client.read_gatt_char(PolarH10.FIRMWARE_REVISION_UUID)
#         self.hardware_revision = await self.bleak_client.read_gatt_char(PolarH10.HARDWARE_REVISION_UUID)
#         self.software_revision = await self.bleak_client.read_gatt_char(PolarH10.SOFTWARE_REVISION_UUID)
    
#     async def print_device_info(self):
#         BLUE = "\033[94m"
#         RESET = "\033[0m"
#         print(f"Model Number: {BLUE}{''.join(map(chr, self.model_number))}{RESET}\n"
#             f"Manufacturer Name: {BLUE}{''.join(map(chr, self.manufacturer_name))}{RESET}\n"
#             f"Serial Number: {BLUE}{''.join(map(chr, self.serial_number))}{RESET}\n"
#             f"Address: {BLUE}{self.bleak_device.address}{RESET}\n"
#             f"Battery Level: {BLUE}{int(self.battery_level[0])}%{RESET}\n"
#             f"Firmware Revision: {BLUE}{''.join(map(chr, self.firmware_revision))}{RESET}\n"
#             f"Hardware Revision: {BLUE}{''.join(map(chr, self.hardware_revision))}{RESET}\n"
#             f"Software Revision: {BLUE}{''.join(map(chr, self.software_revision))}{RESET}")
        


# heart_rate_data = []
# async def heart_rate_handler(sender, data):
#     # El valor de los latidos del corazón se encuentra en el byte 1 del arreglo de datos.
#     heart_rate = data[1]
#     heart_rate_data.append(heart_rate)
#     timestamp = datetime.now().strftime('%H:%M:%S.%f')
#     print("Latidos del corazón:", heart_rate, timestamp)


    


# async def main():
#     devices = await BleakScanner.discover()
#     polar_device_found = False

#     global polar_device

#     for device in devices:
#         print("-------------------")
#         print(device)
#         print("-------------------")
#         if device.name is not None and "Polar" in device.name:
#             polar_device_found = True
#             polar_device = PolarH10(device)
#             await polar_device.connect()
#             await polar_device.get_device_info()
#             await polar_device.print_device_info()



#             async with BleakClient(device) as client:
#                 # UUID de la característica de frecuencia cardíaca
#                 heart_rate_characteristic_uuid = "00002a37-0000-1000-8000-00805f9b34fb"

#                 # Suscribirse a las notificaciones de cambios en la característica de frecuencia cardíaca
#                 await client.start_notify(heart_rate_characteristic_uuid, heart_rate_handler)

            

#                 # Esperar a que se reciban los datos del sensor de frecuencia cardíaca
#                 while True:
#                     await asyncio.sleep(0.1)  # Esperar un corto período de tiempo para recibir notificaciones

    
#     if not polar_device_found:
#         print("No Polar device found")



# loop = asyncio.new_event_loop()
# asyncio.set_event_loop(loop)
# loop.run_until_complete(main())


import biosppy
import pyhrv.time_domain as td
import numpy as np

# Load sample ECG signal
signal = np.loadtxt('./files/SampleECG.txt')[:, -1]

# Get R-peaks series using biosppy
t, filtered_signal, rpeaks = biosppy.signals.ecg.ecg(signal)[:3]

# Compute parameter using R-peak series
results = td.rmssd(rpeaks=t[rpeaks])
