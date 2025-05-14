# Visionova: Spectral Fingerprint Analysis

This project, named Visionova, focuses on reading spectral data from an AS7265X sensor, analyzing it to identify objects based on their unique spectral fingerprints, and providing additional insights like ripeness, Brix levels, potential pesticide presence, and estimated expiry based on weather conditions. It integrates hardware (AS7265X sensor, Arduino/ESP8266, optional OLED display) with Python scripts for data processing, visualization, and analysis.

## Directory Structure
├── openweatherapi.py
├── spectral_fingerprints.json
├── spectral_fingerprints_crazycode.json
├── spectralfingerprint.py
├── spectralfingerprint_oled.py
├── spectralfingerprintwithtestdata.py
├── tempCodeRunnerFile.py
├── testdata.json
└── ARDIUNO CODES/
└── visionova/
└── visionova.ino

## Files Overview

* `openweatherapi.py`: A standalone Python script to fetch current weather data for the user's location using the OpenWeatherMap API and the `geocoder` library.
* `spectral_fingerprints.json`: A JSON file storing known spectral fingerprints (wavelength intensity values) associated with specific object labels. This serves as the primary database for object identification in `spectralfingerprint.py`.
* `spectral_fingerprints_crazycode.json`: Another JSON file containing spectral fingerprints, potentially used for different experiments, objects, or testing scenarios than `spectral_fingerprints.json`.
* `spectralfingerprint.py`: The core Python script for reading spectral data from a serial port (connected to the sensor via Arduino), plotting the spectral curve in real-time using Matplotlib, identifying the object by comparing the measured fingerprint to known ones using Euclidean distance, and providing a command-line interface to label new unknown objects.
* `spectralfingerprint_oled.py`: An advanced version of the spectral analysis script. It incorporates location detection, fetches weather forecasts via the OpenWeatherMap API, calculates estimated Brix, ripeness, and pesticide probability based on the spectral data, predicts expiry dates influenced by weather, and is designed to send this information over serial (likely to an ESP8266 for display on an OLED).
* `spectralfingerprintwithtestdata.py`: A variation of the spectral analysis script that loads its known fingerprints from `testdata.json` instead of `spectral_fingerprints.json`. It focuses on identifying objects based on the test data and displaying associated sample details from that file.
* `tempCodeRunnerFile.py`: A temporary file often created by code editors, typically not part of the main project.
* `testdata.json`: A JSON file containing sample spectral data along with metadata such as sample ID, type, freshness, ripeness, and pesticides. Used by `spectralfingerprintwithtestdata.py`.
* `ARDIUNO CODES/visionova/visionova.ino`: The Arduino (or compatible microcontroller like ESP8266) sketch responsible for interfacing with the AS7265X spectral sensor, reading its data across the 18 wavelengths, formatting the data (likely as comma-separated values), and sending it over the serial port to the connected computer running the Python scripts. It may also receive data from the Python script in the `_oled` version.

## Features

* **Real-time Spectral Data Acquisition:** Reads 18-channel spectral intensity data from an AS7265X sensor.
* **Live Plotting:** Visualizes the spectral curve in real-time using Matplotlib (in `spectralfingerprint.py` and `spectralfingerprintwithtestdata.py`).
* **Object Identification:** Compares measured spectral fingerprints to a database of known fingerprints using Euclidean distance.
* **Confidence Scoring:** Provides a confidence score (Euclidean distance) for the identification.
* **New Object Labeling:** Allows users to manually label unknown objects to expand the database (`spectralfingerprint.py`).
* **Advanced Analysis (`spectralfingerprint_oled.py`):**
    * Location detection for localized weather information.
    * Weather forecast integration to influence expiry predictions.
    * Calculates estimated Brix levels.
    * Determines ripeness stage.
    * Estimates pesticide probability.
    * Predicts expiry dates (both ambient and refrigerated).
    * Sends analysis results over serial, likely for display on an external device like an OLED screen.
* **Test Data Integration (`spectralfingerprintwithtestdata.py`):** Uses a dedicated test dataset for identification and displays rich metadata associated with the identified sample.

## Prerequisites

* **Hardware:**
    * AS7265X Spectral Sensor
    * Arduino or compatible microcontroller (e.g., ESP8266)
    * Connections between sensor and microcontroller, and microcontroller and computer (usually via USB serial).
    * (Optional) OLED display and necessary connections if using `spectralfingerprint_oled.py` with the corresponding Arduino code modifications.
* **Software:**
    * Python 3.x installed on your computer.
    * Arduino IDE installed (to upload `visionova.ino`).
* **Python Libraries:** Install the required libraries using pip:
    ```bash
    pip install pyserial numpy matplotlib scipy scikit-learn requests geocoder geopy pandas tkinter
    ```
    *(Note: `scikit-learn` might be implicitly used for `euclidean` in some environments, but `scipy.spatial.distance.euclidean` is explicitly imported. `tkinter` is usually bundled with Python but listed as it's used for the dialog.)*
* **API Key:** An OpenWeatherMap API key is required for fetching weather data (`openweatherapi.py`, `spectralfingerprint_oled.py`). Obtain one from [https://openweathermap.org/api](https://openweathermap.org/api).

## Setup

1.  **Clone the Repository:** If the code is hosted in a repository, clone it to your local machine.
    ```bash
    git clone <repository_url> nikhil-gorasa-visionova-project
    cd nikhil-gorasa-visionova-project
    ```
    If you just have the files, organize them into the structure shown above.
2.  **Install Python Dependencies:** Navigate to the project root directory in your terminal and run the pip install command mentioned in Prerequisites.
3.  **Hardware Setup:**
    * Connect the AS7265X sensor to your Arduino/microcontroller according to the sensor's documentation and the pin assignments in `visionova.ino`.
    * Connect your Arduino/microcontroller to your computer via USB (which provides the serial connection).
4.  **Upload Arduino Code:** Open `ARDIUNO CODES/visionova/visionova.ino` in the Arduino IDE, select the correct board and COM port, and upload the sketch to your microcontroller.
5.  **Configure API Keys:**
    * Open `openweatherapi.py` and replace `"YOUR_API_KEY_HERE"` (or the existing placeholder) with your actual OpenWeatherMap API key.
    * Open `spectralfingerprint_oled.py` and replace `"YOUR_API_KEY_HERE"` (or the existing placeholder) with your actual OpenWeatherMap API key.
6.  **Identify Serial Port:** Determine the COM port assigned to your connected microcontroller (check Arduino IDE's `Tools > Port` or your operating system's device manager).
7.  **Update Serial Port in Python Scripts:** Open `spectralfingerprint.py`, `spectralfingerprint_oled.py`, and `spectralfingerprintwithtestdata.py`. In each file, find the line like `ser = serial.Serial('COM9', ...)` and change `'COM9'` to your microcontroller's COM port.
8.  **Prepare Fingerprint Data:**
    * For `spectralfingerprint.py`, you can either start with an empty `spectral_fingerprints.json` and label new objects as you encounter them, or manually populate it with known object fingerprints.
    * For `spectralfingerprintwithtestdata.py`, ensure `testdata.json` exists and contains the sample data you want to use for identification.
    * `spectral_fingerprints_crazycode.json` might be for specific testing and may not require initial setup depending on usage.

## Usage

Run the Python scripts from your terminal. Ensure the serial connection is active (microcontroller connected and running the Arduino sketch).

* **Basic Spectral Analysis and Identification (`spectralfingerprint.py`):**
    ```bash
    python spectralfingerprint.py
    ```
    This will start reading data, plot the spectral curve, and print identified objects. If an "Unknown (New Object)" is detected, you can type `l` in the terminal and press Enter to trigger a GUI dialog to label the current fingerprint.
* **Advanced Analysis with OLED Communication (`spectralfingerprint_oled.py`):**
    ```bash
    python spectralfingerprint_oled.py
    ```
    This will read data, identify the object, perform advanced analysis (Brix, ripeness, etc.), use your detected location for weather forecast, and send the results over the serial port. The Matplotlib window might still appear, but the primary output is intended for the serial connection.
* **Analysis using Test Data (`spectralfingerprintwithtestdata.py`):**
    ```bash
    python spectralfingerprintwithtestdata.py
    ```
    This script functions similarly to `spectralfingerprint.py` but uses the data from `testdata.json` as its known fingerprints. It will plot the data and identify objects based *only* on the entries in `testdata.json`.

**Stopping the Scripts:** Press `Ctrl + C` in the terminal where the script is running to gracefully shut it down and close the serial connection and plot windows.

## Hardware

* **AS7265X:** A multi-spectral sensor chip capable of measuring light intensity across 18 visible and near-infrared wavelengths.
* **Arduino/ESP8266:** Microcontroller used to interface with the AS7265X sensor, read its data, and communicate with the computer via serial. An ESP8266 might be preferred for its Wi-Fi capabilities, potentially enabling data transmission or receiving weather data directly, though the current Python script handles weather via the PC's internet connection.
* **OLED Display:** An optional display that the ESP8266 (driven by the serial data from `spectralfingerprint_oled.py`) can use to show the analysis results directly on a device.

## Potential Improvements

* **Calibration:** Implement a proper calibration routine for the AS7265X sensor readings.
* **Robust Identification:** Explore more advanced machine learning classification algorithms (e.g., SVM, k-NN, Neural Networks) for object identification instead of just Euclidean distance.
* **Improved Expiry Model:** Refine the expiry prediction model to account for other factors like humidity, initial freshness, and specific storage conditions beyond just temperature.
* **Full GUI:** Develop a more integrated graphical user interface for all functionalities, including data visualization, labeling, and displaying analysis results, instead of relying on separate plots and terminal output/dialogs.
* **Wireless Communication:** Utilize the ESP8266's Wi-Fi to send data to a local network or cloud service, or receive data/commands.
* **Expand Database:** Collect and add more diverse spectral fingerprints for a wider range of objects.

---

**Project by:** Team Zenith
