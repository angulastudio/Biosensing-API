from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import PlainTextResponse
from bleak import BleakScanner, BleakClient
import asyncio
import struct
import math
from scipy import signal
from scipy.signal import find_peaks
from pyhrv import time_domain
import uvicorn
import numpy as np

app = FastAPI()

class PolarH10:
    # Códigos UUID de los servicios y características de Polar H10
    HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
    HEART_RATE_CHARACTERISTIC_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

    def __init__(self):
        self.bleak_device = None
        self.bleak_client = None
        self.subscribers = []
        self.notifications_started = False

    async def connect(self, device):
        self.bleak_device = device
        self.bleak_client = BleakClient(self.bleak_device)
        await self.bleak_client.connect()

    async def disconnect(self):
        if self.bleak_client:
            await self.bleak_client.disconnect()

    async def start_notifications(self):
        await self.bleak_client.start_notify(
            PolarH10.HEART_RATE_CHARACTERISTIC_UUID,
            self.notification_callback
        )
        self.notifications_started = True

    async def stop_notifications(self):
        await self.bleak_client.stop_notify(
            PolarH10.HEART_RATE_CHARACTERISTIC_UUID
        )
        self.notifications_started = False

    async def notify_subscribers(self, data):
        for subscriber in self.subscribers:
            await subscriber(data)

    async def notification_callback(self, sender, data):
        await self.notify_subscribers(data)

heart_rate_data = []
rr_peaks_data = []
hrv_data = []
polar_device = PolarH10()

# Configuración del filtro
fs = 100  # Frecuencia de muestreo (Hz)
fc = 10  # Frecuencia de corte del filtro (Hz)
order = 4  # Orden del filtro

# Diseñar el filtro Butterworth de lowpass
nyquist_freq = 0.5 * fs
cutoff_freq = fc / nyquist_freq
b, a = signal.butter(order, cutoff_freq, btype='low', analog=False, output='ba')

# Norm HRV
threshold = 70


async def heart_rate_handler(data):
    heart_rate = struct.unpack('<B', data[1:2])[0]
    heart_rate_data.append(heart_rate)

def apply_filter(data):
    filtered_data = signal.lfilter(b, a, data)
    return filtered_data.tolist()

hrv_scoreT = 0

def calculate_hrv(rr_intervals):
    global hrv_scoreT

    if len(rr_intervals) < 2:
        return None

    recent_data = rr_intervals[-4:]
    differences = [rr_intervals[i] - rr_intervals[i-1] for i in range(len(recent_data))]
    squared_differences = [diff ** 2 for diff in differences]
    mean_squared_diff = sum(squared_differences) / (len(squared_differences) - 1)
    rmssd = math.sqrt(mean_squared_diff)

    ln_rmssd = math.log(rmssd)
    hrv_score = (ln_rmssd / 6.5) * 100

    # listt.append(hrv_score)

    # Total Recording HRV
    differencesT = [rr_intervals[i] - rr_intervals[i-1] for i in range(len(rr_intervals))]
    squared_differencesT = [diffT ** 2 for diffT in differencesT]
    mean_squared_diffT = sum(squared_differencesT) / (len(squared_differencesT) - 1)
    rmssdT = math.sqrt(mean_squared_diffT)

    ln_rmssdT = math.log(rmssdT)
    hrv_scoreT = (ln_rmssdT / 6.5) * 100

    # if hrv_score + 15 > listt[-1:][0] or hrv_score -15 <= listt[-1:][0]:
    #     inverted_hrv_score = 100 - hrv_score
    #     print("ENTRE")
    # else:
    #     inverted_hrv_score = hrv_score

    inverted_hrv_score = 100 - hrv_score

    return inverted_hrv_score





def lowpass_filter(signal, cutoff_freq, sampling_freq):
    """
    Aplica un filtro lowpass a la señal.

    Args:
        signal (numpy.ndarray): Señal de entrada.
        cutoff_freq (float): Frecuencia de corte del filtro (en Hz).
        sampling_freq (float): Frecuencia de muestreo de la señal (en Hz).

    Returns:
        numpy.ndarray: Señal filtrada.
    """
    normalized_cutoff_freq = 2 * cutoff_freq / sampling_freq
    b, a = signal.butter(1, normalized_cutoff_freq, 'low', analog=False)
    filtered_signal = signal.lfilter(b, a, signal)
    return filtered_signal



def apply_rr_peak_filter(rr_peaks, window_size=5):
    filtered_rr_peaks = []
    for i in range(len(rr_peaks)):
        start_index = max(0, i - window_size // 2)
        end_index = min(len(rr_peaks), i + window_size // 2 + 1)
        rr_values = rr_peaks[start_index:end_index]
        filtered_rr_value = sum(rr_values) / len(rr_values)
        filtered_rr_peaks.append(filtered_rr_value)
        
    return filtered_rr_peaks


async def rr_peaks_handler(data):
    flags = struct.unpack('<B', data[0:1])[0]
    rr_interval_present = (flags >> 4) & 0x01
    if rr_interval_present:
        rr_interval1 = struct.unpack('<H', data[2:4])[0]
        rr_peaks_data.append(rr_interval1)
            
        filtered_rr_peaks = apply_rr_peak_filter(rr_peaks_data)
        # filtered_rr_peaks = apply_rr_peak_filter(rr_peaks_data[-4:])
        if len(filtered_rr_peaks) >= 2:
            hrv_value = calculate_hrv(filtered_rr_peaks)
            if hrv_value is not None:
                hrv_data.append({"hrv": hrv_value})


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

def calculate_rmssd(rr_intervals):
    """Calcula el RMSSD de una serie de intervalos RR."""
    if len(rr_intervals) < 2:
        return None
    diffs = np.diff(rr_intervals)
    squared_diffs = diffs ** 2
    mean_squared_diffs = np.mean(squared_diffs)
    rmssd_value = np.sqrt(mean_squared_diffs)
    return rmssd_value

def scale_hrv_to_100(ln_rmssd):
    """Escala el ln(RMSSD) a un rango de 0 a 100."""
    # Estos rangos son aproximados y deberían ser ajustados basados en datos empíricos
    min_ln_rmssd = 0
    max_ln_rmssd = 6.5
    scaled_hrv = (ln_rmssd - min_ln_rmssd) / (max_ln_rmssd - min_ln_rmssd) * 100
    return min(max(scaled_hrv, 0), 100)


@app.on_event("shutdown")
async def shutdown_event():
    print("Bye bye, your total HRV: ", hrv_scoreT)
    await polar_device.disconnect()

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )

@app.get("/connect")
async def connect_to_polar():
    try:
        devices = await BleakScanner.discover()
        polar_devices = [device for device in devices if device.name is not None and "Polar" in device.name]
        if not polar_devices:
            raise HTTPException(status_code=404, detail="No Polar devices found")

        await polar_device.connect(polar_devices[0])
        return {"message": "Connected to Polar device"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/start_notifications")
async def start_notifications():
    try:
        if not polar_device.notifications_started:
            polar_device.subscribers.append(heart_rate_handler)
            polar_device.subscribers.append(rr_peaks_handler)
            await polar_device.start_notifications()
            return {"message": "Notifications started"}

        raise HTTPException(status_code=500, detail="Notifications already started")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stop_notifications")
async def stop_notifications():
    try:
        if polar_device.notifications_started:
            polar_device.subscribers.remove(heart_rate_handler)
            polar_device.subscribers.remove(rr_peaks_handler)
            await polar_device.stop_notifications()
            return {"message": "Notifications stopped"}

        raise HTTPException(status_code=500, detail="Notifications already stopped")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/heart_rate")
async def get_heart_rate():
    try:
        if heart_rate_data:
            return {"heart_rate": heart_rate_data[-1]}

        raise HTTPException(status_code=404, detail="No heart rate data available")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rr_peaks")
async def get_rr_peaks():
    try:
        if rr_peaks_data:
            return {"rr_peaks": rr_peaks_data[-1]}

        raise HTTPException(status_code=404, detail="No RR peaks data available")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/hrv")
async def get_hrv():
    try:
        if hrv_data:
            hrv_values = [data["hrv"] for data in hrv_data]
            filtered_hrv_data = apply_filter(hrv_values)
            filtered_hrv = round(filtered_hrv_data[-1], 2)
            return {"hrv": filtered_hrv}

        raise HTTPException(status_code=404, detail="No HRV data available")

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
