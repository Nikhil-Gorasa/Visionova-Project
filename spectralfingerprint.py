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

# File to store known fingerprints
FINGERPRINT_FILE = "spectral_fingerprints.json"

# AS7265X Wavelengths
wavelengths = [410, 435, 460, 485, 510, 535, 560, 585, 610, 
               645, 680, 705, 730, 760, 810, 860, 900, 940]

# Load or initialize known fingerprints
try:
    with open(FINGERPRINT_FILE, "r") as f:
        known_fingerprints = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    known_fingerprints = {}

# Rolling buffer to store past readings
history_size = 3
spectral_history = deque(maxlen=history_size)

# Global flag to trigger labeling
labeling_requested = False

# Distance threshold for identifying known objects
DISTANCE_THRESHOLD = 50.0  # Adjust this based on your data scale

# Try connecting to Serial port
try:
    ser = serial.Serial('COM9', 115200, timeout=2)  # Adjust COM port
except serial.SerialException as e:
    print(f"❌ Serial connection error: {e}")
    exit()

# Function to identify object
def identify_object(measured_fingerprint):
    min_distance = float('inf')
    identified_object = "Unknown"

    for obj_name, ref_fingerprint in known_fingerprints.items():
        distance = euclidean(measured_fingerprint, ref_fingerprint)
        if distance < min_distance:
            min_distance = distance
            identified_object = obj_name
    
    # If the minimum distance exceeds the threshold, classify as Unknown
    if min_distance > DISTANCE_THRESHOLD:
        identified_object = "Unknown (New Object)"
    
    return identified_object, min_distance

# Function to save fingerprints
def save_fingerprint(label, fingerprint):
    known_fingerprints[label] = fingerprint
    with open(FINGERPRINT_FILE, "w") as f:
        json.dump(known_fingerprints, f, indent=4)
    print(f"✅ Saved new fingerprint: {label}")

# GUI function for labeling
def ask_label(fingerprint):
    root = tk.Tk()
    root.withdraw()
    label = simpledialog.askstring("Label Spectral Data", "New object detected! Enter object name:")
    if label:
        save_fingerprint(label, fingerprint)
    root.destroy()

# User input handling (runs in a separate thread)
def check_user_input():
    global labeling_requested
    while True:
        user_input = input().strip().lower()
        if user_input == "l":
            labeling_requested = True

# Setup Matplotlib in Main Thread
plt.ion()
fig = plt.figure(figsize=(15, 6))
gs = GridSpec(1, 2, width_ratios=[2, 1], figure=fig)

# Create subplots
ax = fig.add_subplot(gs[0])  # Main plot
ax_values = fig.add_subplot(gs[1])  # Values panel
ax_values.axis('off')

# Setup main plot
ax.set_xlabel("Wavelength (nm)")
ax.set_ylabel("Intensity")
ax.set_title("Spectral Fingerprint Analysis")
ax.grid(True)

def read_and_plot():
    global labeling_requested
    last_identified_object = None  # Track the last identified object to detect changes

    while True:
        try:
            # Read Serial Data
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue
            
            values = line.split(',')
            if len(values) != 18:
                print(f"⚠️ Invalid data length: {len(values)} | Data: {line}")
                continue

            try:
                values = list(map(float, values))
            except ValueError:
                print(f"⚠️ Data conversion error | Raw Data: {line}")
                continue

            # Identify Object
            identified_object, confidence = identify_object(values)

            # Check if a new object is detected
            if identified_object == "Unknown (New Object)" and identified_object != last_identified_object:
                print(f"❓ New object detected! | Distance: {round(confidence, 2)} (exceeds threshold {DISTANCE_THRESHOLD})")
                print("📝 Please press 'l' to label this new object.")
            elif identified_object != "Unknown (New Object)":
                print(f"🔎 Identified Object: {identified_object} | Confidence Score: {round(confidence, 2)}")

            last_identified_object = identified_object  # Update last identified object

            # Store new data into rolling buffer
            spectral_history.append(values)

            # Update the main plot
            ax.clear()
            for i, spectrum in enumerate(spectral_history):
                alpha = (i + 1) / len(spectral_history)
                ax.plot(wavelengths, spectrum, marker='o', linestyle='-', alpha=alpha)

            # Plot reference fingerprint if not a new object
            if identified_object in known_fingerprints:
                ax.plot(wavelengths, known_fingerprints[identified_object], 
                        marker='x', linestyle='--', color='r', 
                        label=f"Reference: {identified_object}")

            # Update main plot labels
            ax.set_xlabel("Wavelength (nm)")
            ax.set_ylabel("Intensity")
            title = f"Identified: {identified_object} | Distance: {round(confidence, 2)}"
            if identified_object == "Unknown (New Object)":
                title += "\nPress 'l' to label"
            ax.set_title(title)
            ax.legend()
            ax.grid(True)

            # Update values panel
            ax_values.clear()
            ax_values.axis('off')
            value_text = "Current Values:\n\n"
            for wav, val in zip(wavelengths, values):
                value_text += f"{wav}nm: {val:.2f}\n"
            if identified_object == "Unknown (New Object)":
                value_text += "\nNew object! Press 'l' to label."
            ax_values.text(0.1, 0.95, value_text, 
                          transform=ax_values.transAxes,
                          verticalalignment='top',
                          fontfamily='monospace')

            plt.draw()
            plt.pause(0.1)

            # Check if labeling is requested
            if labeling_requested and identified_object == "Unknown (New Object)":
                ask_label(values)
                labeling_requested = False  # Reset the flag

        except serial.SerialException:
            print("❌ Serial connection lost. Trying to reconnect...")
            try:
                ser.close()
                ser.open()
                print("🔄 Reconnected to serial port.")
            except serial.SerialException as e:
                print(f"❌ Failed to reconnect: {e}")
                break

        except KeyboardInterrupt:
            print("\n👋 Exiting gracefully...")
            ser.close()
            plt.close()
            break

# Run user input checking in a separate thread
input_thread = threading.Thread(target=check_user_input)
input_thread.daemon = True
input_thread.start()

# Run plotting in MAIN THREAD
read_and_plot()