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

# AS7265X Wavelengths
wavelengths = [410, 435, 460, 485, 510, 535, 560, 585, 610, 
               645, 680, 705, 730, 760, 810, 860, 900, 940]

# Load or initialize known fingerprints
try:
    with open('testdata.json', 'r') as f:
        test_data = json.load(f)
        # Convert test data to fingerprints format
        known_fingerprints = {
            item['type']: list(item['spectral_values'].values())
            for item in test_data
        }
except (FileNotFoundError, json.JSONDecodeError):
    test_data = []
    known_fingerprints = {}

# Rolling buffer to store past 50 readings
history_size = 3
spectral_history = deque(maxlen=history_size)

# Global flag to trigger labeling
labeling_requested = False

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
    
    return identified_object, min_distance

# Function to save fingerprints
def save_fingerprint(label, fingerprint):
    known_fingerprints[label] = fingerprint
    print(f"✅ Added new fingerprint: {label}")

# GUI function for labeling
def ask_label(fingerprint):
    root = tk.Tk()
    root.withdraw()
    label = simpledialog.askstring("Label Spectral Data", "Enter object name:")
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
fig = plt.figure(figsize=(20, 10))
gs = GridSpec(2, 2, width_ratios=[2, 1], height_ratios=[1, 1])

# Create subplots
ax_main = fig.add_subplot(gs[0, 0])  # Main spectral plot
ax_values = fig.add_subplot(gs[0, 1])  # Values panel
ax_info = fig.add_subplot(gs[1, :])  # Information panel
ax_values.axis('off')
ax_info.axis('off')

# Load test data
def load_test_data():
    with open('testdata.json', 'r') as f:
        return json.load(f)

test_data = load_test_data()

def read_and_plot():
    global labeling_requested

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

            # Print results in Terminal
            print(f"🔎 Identified Object: {identified_object} | Confidence Score: {round(confidence, 2)}")

            # Store new data into rolling buffer
            spectral_history.append(values)

            # Update the main spectral plot
            ax_main.clear()
            for i, spectrum in enumerate(spectral_history):
                alpha = (i + 1) / len(spectral_history)
                ax_main.plot(wavelengths, spectrum, marker='o', linestyle='-', alpha=alpha)

            # Plot reference fingerprint
            if identified_object in known_fingerprints:
                ax_main.plot(wavelengths, known_fingerprints[identified_object], 
                        marker='x', linestyle='--', color='r', 
                        label=f"Reference: {identified_object}")

            # Update main plot labels
            ax_main.set_xlabel("Wavelength (nm)")
            ax_main.set_ylabel("Intensity")
            ax_main.set_title(f"Identified: {identified_object} | Confidence: {round(confidence, 2)}")
            ax_main.legend()
            ax_main.grid(True)

            # Update values panel
            ax_values.clear()
            ax_values.axis('off')
            value_text = "Current Spectral Values:\n\n"
            for wav, val in zip(wavelengths, values):
                value_text += f"{wav}nm: {val:.2f}\n"
            ax_values.text(0.1, 0.95, value_text, 
                          transform=ax_values.transAxes,
                          verticalalignment='top',
                          fontfamily='monospace')

            # Update information panel
            ax_info.clear()
            ax_info.axis('off')
            
            # Find matching sample in test data
            matching_sample = next((item for item in test_data 
                                 if item['type'] == identified_object), None)
            
            if matching_sample:
                info_text = (
                    f"Sample Details:\n\n"
                    f"Sample ID: {matching_sample['sample_id']}\n"
                    f"Type: {matching_sample['type']}\n"
                    f"Freshness: {matching_sample['freshness']}\n"
                    f"Ripeness: {matching_sample['ripeness']}\n"
                    f"Pesticides: {matching_sample['pesticides']}\n"
                )
            else:
                info_text = "No matching sample found in database"

            ax_info.text(0.1, 0.95, info_text,
                        transform=ax_info.transAxes,
                        verticalalignment='top',
                        fontfamily='monospace',
                        fontsize=12)

            plt.tight_layout()
            plt.draw()
            plt.pause(0.1)

            # Check if labeling is requested
            if labeling_requested:
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
                break  # Exit the loop if reconnection fails

        except KeyboardInterrupt:
            print("\n👋 Exiting gracefully...")
            ser.close()
            plt.close()
            break

# Run user input checking in a separate thread
input_thread = threading.Thread(target=check_user_input)
input_thread.daemon = True  # Allows the program to exit even if this thread is running
input_thread.start()

# Run plotting in MAIN THREAD (fixes Matplotlib GUI issue)
read_and_plot()
