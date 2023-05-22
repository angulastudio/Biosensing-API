from flask import render_template, jsonify
from bleak import BleakScanner, BleakClient
import asyncio
from datetime import datetime
import connexion
# from connexion import FlaskApp
from polar import PolarH10


# app = FlaskApp(__name__, specification_dir="./")
# app.add_api("swagger.yml")


def connect():
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
                loop.run_until_complete(polar_device.print_device_info())
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

if __name__ == '__main__':
    app = connexion.FlaskApp(__name__, specification_dir="./")
    app.add_api("swagger.yml")

    app.add_url_rule("/connect", "connect", connect, methods=["GET"])
    app.add_url_rule("/device_info", "get_device_info", get_device_info, methods=["GET"])

    app.run(debug=True, port=8000)
