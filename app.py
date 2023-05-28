from flask import render_template, jsonify, Response, stream_with_context, make_response, Flask
from bleak import BleakScanner, BleakClient
import asyncio
import connexion
from datetime import datetime
import time




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
        await self.bleak_client.connect_device()


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
        heart_rate = list(heart_rate_data)[1]
        print(heart_rate)
        return heart_rate
    
    async def stream_heart_rate2(self):
        while True:
            heart_rate_data = await self.bleak_client.read_gatt_char(PolarH10.HEART_RATE_CHARACTERISTIC_UUID)
            heart_rate = heart_rate_data[1]
            yield str(heart_rate)
            await asyncio.sleep(1)





polar_device = None
    
async def connect():
    global polar_device
    global polar_device2


    devices = await BleakScanner.discover()
    polar_device_found = False

    for device in devices:
        if device.name is not None and "Polar" in device.name:
            polar_device_found = True
            polar_device = PolarH10(device)
            polar_device2 = device

            try:
                await polar_device.connect_device()

                return 'Conectado al Polar H10'
            except Exception as e:
                return f'Error al conectar con el Polar H10: {str(e)}', 500

    if not polar_device_found:
        return 'No se encontró un dispositivo Polar', 404


def get_device_info():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    devices = loop.run_until_complete(BleakScanner.discover())
    polar_device_found = False

    for device in devices:
        if device.name is not None and "Polar" in device.name:
            polar_device_found = True
            polar_device = PolarH10(device)
            try:
                loop.run_until_complete(polar_device.connect_device())
                loop.run_until_complete(polar_device.get_device_info_())
                device_info = {
                    'model_number': ''.join(map(chr, polar_device.model_number)).replace('\x0000', ''),
                    'manufacturer_name': ''.join(map(chr, polar_device.manufacturer_name)),
                    'serial_number': ''.join(map(chr, polar_device.serial_number)),
                    'battery_level': int(polar_device.battery_level[0]),
                    'firmware_revision': ''.join(map(chr, polar_device.firmware_revision)),
                    'hardware_revision': ''.join(map(chr, polar_device.hardware_revision)),
                    'software_revision': ''.join(map(chr, polar_device.software_revision))
                }
                return jsonify(device_info)
            except Exception as e:
                return f'Error al obtener la información del dispositivo: {str(e)}', 500

    if not polar_device_found:
        return 'No se encontró un dispositivo Polar', 404
    


# async def stream_heart_rate():
#     global polar_device

#     if not polar_device:
#         return 'No se ha conectado ningún dispositivo Polar', 404

#     async def heart_rate_stream():
#         while True:
#             heart_rate = await polar_device.stream_heart_rate2()
#             yield str(heart_rate) + '\n'

#     async def stream():
#         async for data in heart_rate_stream():
#             yield data

#     async def main():
#         event_loop = asyncio.get_event_loop()
#         return await event_loop.run_until_complete(stream())

#     asyncio.get_event_loop().run_until_complete(main())


async def stream_heart_rate():
    async def generate_heart_rate():
        while True:
            if polar_device is not None:
                try:
                    heart_rate = await polar_device.read_heart_rate()
                    timestamp = datetime.now().strftime('%H:%M:%S.%f')
                    heart_rate_data = f"Latidos del corazón: {heart_rate}, {timestamp}"
                    yield heart_rate_data

                except Exception as e:
                    print(f'Error al leer el ritmo cardíaco: {str(e)}')

            else:
                heart_rate_data = "No se encontró un dispositivo Polar"
                yield heart_rate_data

            await asyncio.sleep(1)

    response = Response(generate_heart_rate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    return response





if __name__ == '__main__':
    app = connexion.FlaskApp(__name__, specification_dir="./")
    app.add_api("swagger.yml")

    app.add_url_rule("/connect", "connect", connect, methods=["GET"])
    app.add_url_rule("/device_info", "get_device_info", get_device_info, methods=["GET"])
    app.add_url_rule("/heart_rate", "stream_heart_rate", stream_heart_rate, methods=["GET"])

    app.run(debug=True, port=8000, threaded=True)
