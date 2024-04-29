# from fastapi import FastAPI, HTTPException
# from fastapi.responses import JSONResponse
# from starlette.responses import StreamingResponse
# from bleak import BleakScanner, BleakClient
# # from polar import PolarH10
# import asyncio
# import uvicorn
# import struct
# from pyhrv import time_domain
# import math


from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from bleak import BleakScanner
from bleak import BleakScanner, BleakClient
from typing import List
import asyncio

app = FastAPI()


@app.get("/scan")
async def scan_devices():
    devices = await BleakScanner.discover()
    polar_devices = [{"name": device.name, "address": device.address} for device in devices if device.name and "Polar" in device.name]

    if not polar_devices:
        raise HTTPException(status_code=404, detail="No se encontraron dispositivos Polar.")

    return polar_devices


async def list_characteristics(device_address: str):
    characteristics_info = []
    async with BleakClient(device_address) as client:
        is_connected = await client.is_connected()
        if is_connected:
            services = await client.get_services()
            for service in services:
                for characteristic in service.characteristics:
                    char_info = {
                        "service_uuid": service.uuid,
                        "characteristic_uuid": characteristic.uuid,
                        "properties": characteristic.properties
                    }
                    characteristics_info.append(char_info)
        else:
            raise Exception("No se pudo conectar al dispositivo.")
    return characteristics_info

@app.get("/characteristics/{device_address}")
async def get_characteristics(device_address: str):
    try:
        characteristics = await list_characteristics(device_address)
        return characteristics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



async def scan_and_connect() -> List[str]:
    print("Escaneando dispositivos BLE disponibles...")
    devices = await BleakScanner.discover()
    # polar_devices = [device for device in devices if "Polar" in device.name]
    polar_devices = [device for device in devices if device.name and "Polar" in device.name]


    if not polar_devices:
        print("No se encontraron dispositivos Polar.")
        return

    print("Dispositivos Polar encontrados:")
    for index, device in enumerate(polar_devices):
        print(f"{index}: {device.name} - {device.address}")

    choice = int(input("Selecciona el dispositivo a conectar (número): "))
    device_to_connect = polar_devices[choice]

    print(f"Conectando a {device_to_connect.name}...")
    async with BleakClient(device_to_connect.address) as client:
        is_connected = await client.is_connected()
        print(f"Conectado a {device_to_connect.name}: {is_connected}")

    return device_to_connect.name


# HEART_RATE_SERVICE_UUID = "180D"
# HEART_RATE_MEASUREMENT_CHAR_UUID = "2A37"
HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HEART_RATE_MEASUREMENT_CHAR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

# async def read_heart_rate(device_address: str):
#     async with BleakClient(device_address) as client:
#         is_connected = await client.is_connected()
#         if is_connected:
#             await client.get_services()
#             # Asegúrate de que el UUID de la característica existe en los servicios descubiertos
#             if HEART_RATE_MEASUREMENT_CHAR_UUID in [char.uuid for service in client.services for char in service.characteristics]:
#                 await client.start_notify(HEART_RATE_MEASUREMENT_CHAR_UUID, heart_rate_notification_handler)
#                 await asyncio.sleep(30)  # Mantener la suscripción activa durante 30 segundos
#                 await client.stop_notify(HEART_RATE_MEASUREMENT_CHAR_UUID)
#             else:
#                 print(f"La característica con UUID {HEART_RATE_MEASUREMENT_CHAR_UUID} no se encontró en el dispositivo.")
#         else:
#             print("No se pudo conectar al dispositivo.")
async def read_heart_rate(device_address: str):
    async with BleakClient(device_address) as client:
        is_connected = await client.is_connected()
        if is_connected:
            await client.start_notify(HEART_RATE_MEASUREMENT_CHAR_UUID, heart_rate_notification_handler)
            await asyncio.sleep(30)  # Mantener la suscripción activa durante 30 segundos
            await client.stop_notify(HEART_RATE_MEASUREMENT_CHAR_UUID)
        else:
            print("No se pudo conectar al dispositivo.")

def heart_rate_notification_handler(sender, data):
    # Aquí se manejarían los datos recibidos
    print(f"Heart Rate Data: {b'data'}")


@app.get("/heartrate/{device_address}")
async def get_heart_rate(device_address: str):
    return await read_heart_rate(device_address)







if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)