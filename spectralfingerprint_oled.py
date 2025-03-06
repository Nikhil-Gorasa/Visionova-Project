import serial
import numpy as np
import matplotlib.pyplot as plt
import json
import tkinter as tk
from tkinter import simpledialog
from scipy.spatial.distance import euclidean
from collections import deque
import threading
from matplotlib.gridspec import GridSpec
import pandas as pd
import requests  # For weather API calls
import sys
from queue import Queue
from threading import Event
from geopy.geocoders import Nominatim
import socket
import requests

# File to store known fingerprints
FINGERPRINT_FILE = "spectral_fingerprints.json"

# AS7265X Wavelengths
wavelengths = [410, 435, 460, 485, 510, 535, 560, 585, 610, 
               645, 680, 705, 730, 760, 810, 860, 900, 940]

# Load known fingerprints
try:
    with open(FINGERPRINT_FILE, "r") as f:
        known_fingerprints = json.load(f)
    print(f"✅ Loaded fingerprints from {FINGERPRINT_FILE}")
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"⚠️ Could not load {FINGERPRINT_FILE}: {e}. Starting with empty fingerprints.")
    known_fingerprints = {}

# Rolling buffer
history_size = 3
spectral_history = deque(maxlen=history_size)

# Global flag for labeling
labeling_requested = False

# Distance threshold
DISTANCE_THRESHOLD = 150.0

# Serial connection
try:
    ser = serial.Serial('COM9', 115200, timeout=2)  # Adjust COM port
except serial.SerialException as e:
    print(f"❌ Serial connection error: {e}")
    exit()

WEATHER_API_KEY = "1970c66b9d0c1cb45130e5da6a5dce31"
WEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5/forecast"

# Typical Brix ranges
BRIX_RANGES = {
    "Lemon": (8, 12), "Apple": (10, 15), "Green Grape": (15, 25), "Orange": (10, 20),
    "Tomato": (4, 6), "Carrot": (6, 10), "Sweet Potato (Matti)": (5, 10),
    "Sweet Potato (Without Matti)": (5, 10), "Potato": (3, 6)
}

# Optimal storage conditions (temp in °C, shelf life in days outside fridge at optimal temp)
STORAGE_CONDITIONS = {
    "Lemon": {"optimal_temp": 10, "max_temp": 15, "outside_days": 30, "fridge_days": 60},
    "Apple": {"optimal_temp": 0, "max_temp": 4, "outside_days": 30, "fridge_days": 90},
    "Green Grape": {"optimal_temp": 0, "max_temp": 2, "outside_days": 14, "fridge_days": 28},
    "Orange": {"optimal_temp": 2, "max_temp": 7, "outside_days": 30, "fridge_days": 60},
    "Tomato": {"optimal_temp": 13, "max_temp": 20, "outside_days": 30, "fridge_days": 14},
    "Carrot": {"optimal_temp": 0, "max_temp": 2, "outside_days": 28, "fridge_days": 120},
    "Sweet Potato (Matti)": {"optimal_temp": 13, "max_temp": 16, "outside_days": 90, "fridge_days": 30},
    "Sweet Potato (Without Matti)": {"optimal_temp": 13, "max_temp": 16, "outside_days": 90, "fridge_days": 30},
    "Potato": {"optimal_temp": 7, "max_temp": 10, "outside_days": 90, "fridge_days": 30}
}

# Function to fetch 7-day weather forecast
def get_weather_forecast(lat, lon):
    try:
        url = f"{WEATHER_BASE_URL}?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            daily_forecasts = []
            
            # Check if we have forecast data
            if "list" in data and len(data["list"]) > 0:
                # Get forecasts for next 5 days (more reliable than 7 days)
                for i in range(0, min(40, len(data["list"])), 8):  # 3-hour intervals
                    try:
                        temp = data["list"][i]["main"]["temp"]
                        humidity = data["list"][i]["main"]["humidity"]
                        daily_forecasts.append({"temp": temp, "humidity": humidity})
                    except (KeyError, IndexError):  
                        continue
                
                return daily_forecasts if daily_forecasts else None
            
        print(f"⚠️ Weather data unavailable")
        return None
        
    except Exception as e:
        print(f"⚠️ Weather API error: {e}")
        return None

# Function to predict expiry
def predict_expiry(identified_object, weather_forecast):
    if identified_object not in STORAGE_CONDITIONS:
        return "N/A", "N/A"
    
    conditions = STORAGE_CONDITIONS[identified_object]
    base_outside_days = conditions["outside_days"]
    fridge_days = conditions["fridge_days"]

    # If no weather data, return base values
    if not weather_forecast:
        return f"{base_outside_days}", f"{fridge_days}"
    
    # Rest of the function remains the same
    optimal_temp = conditions["optimal_temp"]
    max_temp = conditions["max_temp"]
    outside_days = base_outside_days
    
    for day in weather_forecast:
        temp = day["temp"]
        if temp > max_temp:
            reduction = (temp - max_temp) * 0.1 * base_outside_days
            outside_days = max(0, outside_days - reduction)
        if outside_days <= 0:
            break
    
    return f"{int(outside_days)}", f"{fridge_days}"

# Brix calculation
def calculate_brix(fingerprint, identified_object):
    if identified_object == "Normal State" or identified_object == "Unknown (New Object)":
        return "N/A"
    nir_avg = np.mean([fingerprint[15], fingerprint[16], fingerprint[17]])
    a, b = 0.05, 0
    if identified_object in BRIX_RANGES:
        min_brix, max_brix = BRIX_RANGES[identified_object]
        a = 0.02 if identified_object == "Lemon" else 0.06
        brix = a * nir_avg + b
        return max(min_brix, min(brix, max_brix))
    return min(a * nir_avg + b, 25)

# Ripeness determination
def determine_ripeness(fingerprint, identified_object):
    if identified_object == "Normal State" or identified_object == "Unknown (New Object)":
        return "N/A"
    chlorophyll_avg = np.mean([fingerprint[4], fingerprint[5], fingerprint[10]])
    carotenoid_avg = np.mean([fingerprint[7], fingerprint[8]])
    ripeness_ratio = carotenoid_avg / (chlorophyll_avg + 1e-6)
    if ripeness_ratio < 1.5:
        return "Unripe"
    elif ripeness_ratio < 3.0:
        return "Ripe"
    else:
        return "Overripe"

# Pesticide detection
def detect_pesticides(fingerprint, ref_fingerprint, identified_object):
    if identified_object == "Normal State" or identified_object == "Unknown (New Object)" or ref_fingerprint is None:
        return "N/A"
    diff = np.abs(np.array(fingerprint[:9]) - np.array(ref_fingerprint[:9]))
    anomaly_score = np.mean(diff) / 100
    return min(100, anomaly_score * 50)

# Identify object and calculate parameters
def identify_object(measured_fingerprint, lat, lon):
    min_distance = float('inf')
    identified_object = "Unknown"
    ref_fingerprint = None

    for obj_name, ref_fingerprint_candidate in known_fingerprints.items():
        distance = euclidean(measured_fingerprint, ref_fingerprint_candidate)
        if distance < min_distance:
            min_distance = distance
            identified_object = obj_name
            ref_fingerprint = ref_fingerprint_candidate
    
    if min_distance > DISTANCE_THRESHOLD:
        identified_object = "Unknown (New Object)"
        ref_fingerprint = None
    
    weather_forecast = get_weather_forecast(lat, lon)
    brix = calculate_brix(measured_fingerprint, identified_object)
    ripeness = determine_ripeness(measured_fingerprint, identified_object)
    pesticide_prob = detect_pesticides(measured_fingerprint, ref_fingerprint, identified_object)
    outside_days, fridge_days = predict_expiry(identified_object, weather_forecast)
    
    return identified_object, min_distance, brix, ripeness, pesticide_prob, outside_days, fridge_days

# Save fingerprints
def save_fingerprint(label, fingerprint):
    known_fingerprints[label] = fingerprint
    with open(FINGERPRINT_FILE, "w") as f:
        json.dump(known_fingerprints, f, indent=4)
    print(f"✅ Saved new fingerprint: {label}")

# GUI for labeling
def ask_label(fingerprint):
    root = tk.Tk()
    root.withdraw()
    label = simpledialog.askstring("Label Spectral Data", "New object detected! Enter object name:")
    if label:
        save_fingerprint(label, fingerprint)
    root.destroy()

# User input handling
input_queue = Queue()
stop_event = Event()

def check_user_input():
    """Thread-safe input handler"""
    while not stop_event.is_set():
        try:
            if sys.stdin.isatty():  # Only try to read input if running in terminal
                user_input = input().strip().lower()
                input_queue.put(user_input)
            else:
                stop_event.wait(1)  # Wait a bit if no terminal
        except EOFError:
            break
        except Exception as e:
            print(f"Input error: {e}")
            break

# Setup Matplotlib
plt.ion()
fig = plt.figure(figsize=(15, 8))
gs = GridSpec(1, 2, width_ratios=[2, 1], figure=fig)

ax = fig.add_subplot(gs[0])
ax_values = fig.add_subplot(gs[1])
ax_values.axis('off')

ax.set_xlabel("Wavelength (nm)")
ax.set_ylabel("Intensity")
ax.set_title("Spectral Fingerprint Analysis")
ax.grid(True)

# Function to get system location
def get_system_location():
    try:
        geolocator = Nominatim(user_agent="geoapiExercises")
        ip_address = requests.get('https://api64.ipify.org?format=json').json()["ip"]
        location = geolocator.geocode(ip_address)
        return location.latitude, location.longitude
    except Exception as e:
        print(f"⚠️ Location error: {e}")
        return 0.0, 0.0

# Modify the read_and_plot function
def read_and_plot():
    global labeling_requested
    last_identified_object = None
    
    # Get system location once at start
    lat, lon = get_system_location()
    print(f"📍 System Location: {lat:.6f}, {lon:.6f}")

    while not stop_event.is_set():
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue
            
            values = line.split(',')
            if len(values) == 18:  # Now expecting only 18 spectral values
                try:
                    spectral_values = list(map(float, values))
                    
                    # Use system location for identification
                    identified_object, confidence, brix, ripeness, pesticide_prob, outside_days, fridge_days = identify_object(spectral_values, lat, lon)
                    
                    # Rest of your existing code...
                    if identified_object != last_identified_object:
                        data_to_send = f"{identified_object},{brix},{ripeness},{pesticide_prob},{outside_days},{fridge_days}\n"
                        print(f"📤 Sending to ESP8266: {data_to_send.strip()}")
                        ser.write(data_to_send.encode('utf-8'))
                        last_identified_object = identified_object

                    # Update display with system location
                    value_text = f"Object: {identified_object}\n"
                    value_text += f"Location: {lat:.6f}, {lon:.6f}\n"
                    # ... rest of your display code ...

                except ValueError as e:
                    print(f"⚠️ Data conversion error: {e}")
                    continue
            else:
                print(f"⚠️ Invalid data length: {len(values)} | Expected: 18")
                continue

            # ... rest of your existing code ...

        except serial.SerialException:
            print("❌ Serial connection lost. Reconnecting...")
            try:
                ser.close()
                ser.open()
            except serial.SerialException as e:
                print(f"❌ Failed to reconnect: {e}")
                stop_event.set()
                break

        except KeyboardInterrupt:
            stop_event.set()
            break

if __name__ == "__main__":
    try:
        # Start input thread
        input_thread = threading.Thread(target=check_user_input)
        input_thread.daemon = True
        input_thread.start()

        # Run main loop
        read_and_plot()

    except KeyboardInterrupt:
        print("\n👋 Gracefully shutting down...")
    finally:
        # Cleanup
        stop_event.set()
        if 'ser' in globals():
            ser.close()
        plt.close('all')
        
        # Wait for input thread to finish
        if input_thread.is_alive():
            input_thread.join(timeout=1.0)