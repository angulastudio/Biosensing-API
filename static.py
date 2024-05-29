from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from bleak import BleakClient
import asyncio
import numpy as np
import uvicorn

app = FastAPI()

class DeviceAddress(BaseModel):
    address: str

# Variable global para almacenar la dirección del dispositivo
ADDRESS = None
UUID_HEART_RATE = "00002a37-0000-1000-8000-00805f9b34fb"

heart_rate_data = []
rr_peaks_data = []
hrv_data = []
bleak_client = None

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
    min_ln_rmssd = 0
    max_ln_rmssd = 6.5
    scaled_hrv = (ln_rmssd - min_ln_rmssd) / (max_ln_rmssd - min_ln_rmssd) * 100
    return min(max(scaled_hrv, 0), 100)

def hr_notification_handler(sender, data):
    """Maneja las notificaciones de HR y RR intervals."""
    hr_value, new_rr_intervals = parse_heart_rate_data(data)
    if hr_value is not None:
        heart_rate_data.append(hr_value)
        print(f"Heart Rate: {hr_value} BPM")
    if new_rr_intervals:
        rr_peaks_data.extend(new_rr_intervals)
        cleaned_rr_intervals = clean_rr_intervals(rr_peaks_data)
        rmssd = calculate_rmssd(cleaned_rr_intervals)
        if rmssd is not None:
            ln_rmssd = np.log(rmssd)
            scaled_hrv = scale_hrv_to_100(ln_rmssd)
            hrv_data.append({"hrv": scaled_hrv})
            print(f"Cleaned RMSSD: {rmssd:.2f} ms, Scaled HRV: {scaled_hrv:.2f}")

@app.post("/set_address")
async def set_address(device_address: DeviceAddress):
    global ADDRESS
    ADDRESS = device_address.address
    return {"message": f"Device address set to {ADDRESS}"}

@app.get("/connect")
async def connect_to_polar():
    try:
        global bleak_client
        if not ADDRESS:
            raise HTTPException(status_code=400, detail="Device address not set")
        bleak_client = BleakClient(ADDRESS)
        await bleak_client.connect()
        return {"message": "Connected to Polar device"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/start_notifications")
async def start_notifications():
    try:
        if bleak_client and not bleak_client.is_connected:
            raise HTTPException(status_code=500, detail="Client is not connected")
        await bleak_client.start_notify(UUID_HEART_RATE, hr_notification_handler)
        return {"message": "Notifications started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stop_notifications")
async def stop_notifications():
    try:
        if bleak_client and bleak_client.is_connected:
            await bleak_client.stop_notify(UUID_HEART_RATE)
            return {"message": "Notifications stopped"}
        raise HTTPException(status_code=500, detail="Client is not connected")
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

# @app.get("/hrv")
# async def get_hrv():
#     try:
#         if hrv_data:
#             return {"hrv": hrv_data[-1]}
#         raise HTTPException(status_code=404, detail="No HRV data available")
#     except Exception as e:
#         return {"error": str(e)}
    
@app.get("/hrv")
async def get_hrv():
    try:
        if hrv_data:
            last_10_hrv = [data["hrv"] for data in hrv_data[-10:]]
            average_hrv = sum(last_10_hrv) / len(last_10_hrv)
            return {"hrv": round(average_hrv, 2)}
        raise HTTPException(status_code=404, detail="No HRV data available")
    except Exception as e:
        return {"error": str(e)}


@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down")
    if bleak_client and bleak_client.is_connected:
        await bleak_client.disconnect()
    if hrv_data:
        all_hrv = [data["hrv"] for data in hrv_data]
        average_hrv = sum(all_hrv) / len(all_hrv)
        print(f"Final average HRV: {average_hrv:.2f}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)