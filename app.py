from flask import render_template, jsonify, Response, stream_with_context
from bleak import BleakScanner, BleakClient
import asyncio
import base64
from datetime import datetime
import connexion
import redis
import time
from polar import PolarH10


heart_rate_data_key = 'heart_rate_data'
r = redis.Redis()
polar_device = None
polar_device2 = None

# def connect():
#     global polar_device

#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)

#     devices = loop.run_until_complete(BleakScanner.discover())
#     polar_device_found = False

#     for device in devices:
#         if device.name is not None and "Polar" in device.name:
#             polar_device_found = True
#             polar_device = PolarH10(device)
#             try:
#                 loop.run_until_complete(polar_device.connect_device())
#                 loop.run_until_complete(polar_device.get_device_info_())
#                 loop.run_until_complete(polar_device.print_device_info())
#                 return 'Conectado al Polar H10'
#             except Exception as e:
#                 return f'Error al conectar con el Polar H10: {str(e)}', 500

#     if not polar_device_found:
#         return 'No se encontró un dispositivo Polar', 404

async def heart_rate_handler(sender, data):
    # El valor de los latidos del corazón se encuentra en el byte 1 del arreglo de datos.
    heart_rate = data[1]
    timestamp = datetime.now().strftime('%H:%M:%S.%f')
    print("Latidos del corazón:", heart_rate, timestamp)
    return("Latidos del corazón:", heart_rate, timestamp)

    
async def connect():
    global polar_device
    global polar_device2

    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)

    devices = await BleakScanner.discover()
    polar_device_found = False

    for device in devices:
        if device.name is not None and "Polar" in device.name:
            polar_device_found = True
            polar_device = PolarH10(device)
            polar_device2 = device
            try:
                await polar_device.connect_device()

                # async with BleakClient(device) as client:
                #     # UUID de la característica de frecuencia cardíaca
                #     heart_rate_characteristic_uuid = "00002a37-0000-1000-8000-00805f9b34fb"

                #     # Suscribirse a las notificaciones de cambios en la característica de frecuencia cardíaca
                #     await client.start_notify(heart_rate_characteristic_uuid, heart_rate_handler)

                

                #     # Esperar a que se reciban los datos del sensor de frecuencia cardíaca
                #     while True:
                #         await asyncio.sleep(0.1)  # Esperar un corto período de tiempo para recibir notificaciones

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
    


def stream_heart_rate():
    def generate_heart_rate():
        while True:
            if polar_device is not None:
                try:
                    heart_rate = polar_device.read_heart_rate()
                    timestamp = datetime.now().strftime('%H:%M:%S.%f')
                    heart_rate_data = f"Latidos del corazón: {heart_rate}, {timestamp}"
                    yield heart_rate_data

                except Exception as e:
                    print(f'Error al leer el ritmo cardíaco: {str(e)}')

            else:
                heart_rate_data = "No se encontró un dispositivo Polar"
                yield heart_rate_data

            time.sleep(1)

    return Response(generate_heart_rate(), mimetype='text/plain')



if __name__ == '__main__':
    app = connexion.FlaskApp(__name__, specification_dir="./")
    app.add_api("swagger.yml")

    app.add_url_rule("/connect", "connect", connect, methods=["GET"])
    app.add_url_rule("/device_info", "get_device_info", get_device_info, methods=["GET"])
    app.add_url_rule("/heart_rate", "stream_heart_rate", stream_heart_rate, methods=["GET"])

    asyncio.run(app.run(debug=True, port=8000))
