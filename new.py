# import asyncio
# from bleak import BleakClient

# address = "D12EA708-D2E2-A337-3E1B-C75976067C2F"
# UUID_HEART_RATE = "00002a37-0000-1000-8000-00805f9b34fb"  # UUID estándar para Heart Rate

# def parse_heart_rate_data(data):
#     """Parsea los datos de frecuencia cardíaca recibidos desde el dispositivo."""
#     flag = data[0]
#     hr_format = flag & 0x01  # Si es 0, HR es UINT8. Si es 1, HR es UINT16.
#     rr_present = (flag & 0x10) >> 4  # Si es 1, los datos de RR están presentes.

#     hr_value = None
#     rr_values = []
#     index = 1  # Comienza después de los flags

#     if hr_format == 0:
#         hr_value = data[index]  # HR es UINT8
#         index += 1
#     else:
#         hr_value = data[index] + (data[index + 1] << 8)  # HR es UINT16
#         index += 2

#     if rr_present == 1:
#         # Extraer todos los valores RR que siguen
#         while index < len(data):
#             rr_value = data[index] + (data[index + 1] << 8)
#             rr_values.append(rr_value)
#             index += 2

#     return hr_value, rr_values

# async def run(address):
#     async with BleakClient(address) as client:
#         if await client.is_connected():
#             print("Connected to the Polar H10")

#             def callback(sender, data):
#                 hr_value, rr_intervals = parse_heart_rate_data(data)
#                 print(f"Heart Rate: {hr_value} BPM")
#                 print("Received RR intervals:", rr_intervals)

#             await client.start_notify(UUID_HEART_RATE, callback)
#             await asyncio.sleep(30)  # Escuchar durante 30 segundos
#             await client.stop_notify(UUID_HEART_RATE)

# loop = asyncio.get_event_loop()
# loop.run_until_complete(run(address))



import asyncio
from bleak import BleakClient
import numpy as np

# Configuración del dispositivo y UUIDs
address = "D12EA708-D2E2-A337-3E1B-C75976067C2F"
UUID_HEART_RATE = "00002a37-0000-1000-8000-00805f9b34fb"

# Variables para almacenar los datos de RR y HR
rr_intervals = []
hr_values = []

# Función para parsear los datos de frecuencia cardíaca
def parse_heart_rate_data(data):
    """Parsea los datos de frecuencia cardíaca recibidos desde el dispositivo."""
    flag = data[0]
    hr_format = flag & 0x01
    rr_present = (flag & 0x10) >> 4

    hr_value = None
    rr_values = []
    index = 1

    if hr_format == 0:
        hr_value = data[index]
        index += 1
    else:
        hr_value = data[index] + (data[index + 1] << 8)
        index += 2

    if rr_present == 1:
        while index < len(data):
            rr_interval = data[index] + (data[index + 1] << 8)
            rr_values.append(rr_interval / 1024.0 * 1000)  # Convert to ms
            index += 2

    return hr_value, rr_values

# Función para limpiar outliers de los RR intervals
def clean_rr_intervals(rr_intervals):
    """Limpia los RR intervals para eliminar artefactos."""
    if len(rr_intervals) < 3:
        return rr_intervals  # No hay suficientes datos para limpiar
    rr_intervals = np.array(rr_intervals)
    q25, q75 = np.percentile(rr_intervals, [25, 75])
    iqr = q75 - q25
    lower_bound = q25 - (1.5 * iqr)
    upper_bound = q75 + (1.5 * iqr)
    return rr_intervals[(rr_intervals > lower_bound) & (rr_intervals < upper_bound)].tolist()

# Función para calcular el RMSSD
def calculate_rmssd(rr_intervals):
    """Calcula el RMSSD de una serie de intervalos RR."""
    if len(rr_intervals) < 2:
        return None
    diffs = np.diff(rr_intervals)
    squared_diffs = diffs ** 2
    mean_squared_diffs = np.mean(squared_diffs)
    rmssd_value = np.sqrt(mean_squared_diffs)
    return rmssd_value

# Función para escalar el ln(RMSSD) a una puntuación de 0-100
def scale_hrv_to_100(ln_rmssd):
    """Escala el ln(RMSSD) a un rango de 0 a 100."""
    # Estos rangos son aproximados y deberían ser ajustados basados en datos empíricos
    min_ln_rmssd = 0
    max_ln_rmssd = 6.5
    scaled_hrv = (ln_rmssd - min_ln_rmssd) / (max_ln_rmssd - min_ln_rmssd) * 100
    return min(max(scaled_hrv, 0), 100)

# Función callback para el manejo de notificaciones de la frecuencia cardíaca
def hr_notification_handler(sender, data):
    """Maneja las notificaciones de HR y RR intervals."""
    hr_value, new_rr_intervals = parse_heart_rate_data(data)
    if hr_value:
        hr_values.append(hr_value)
        print(f"Heart Rate: {hr_value} BPM")
    if new_rr_intervals:
        rr_intervals.extend(new_rr_intervals)
        cleaned_rr_intervals = clean_rr_intervals(rr_intervals)
        rmssd = calculate_rmssd(cleaned_rr_intervals)
        if rmssd:
            ln_rmssd = np.log(rmssd)
            scaled_hrv = scale_hrv_to_100(ln_rmssd)
            print(f"Cleaned RMSSD: {rmssd:.2f} ms, Scaled HRV: {scaled_hrv:.2f}")

async def run(address):
    """Conecta con el dispositivo y maneja la recolección de datos."""
    async with BleakClient(address) as client:
        if await client.is_connected():
            print("Connected to the device")
            await client.start_notify(UUID_HEART_RATE, hr_notification_handler)
            # await asyncio.sleep(30)  # Recolectar datos durante 30 segundos
            await asyncio.sleep(500) 
            await client.stop_notify(UUID_HEART_RATE)
            print("Disconnected from the device")

# Inicia el script
if __name__ == "__main__":
    asyncio.run(run(address))





