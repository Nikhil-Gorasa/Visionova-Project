import requests
import geocoder  # Install using: pip install geocoder

# OpenWeatherMap API key (Replace with your actual API key)
API_KEY = "1970c66b9d0c1cb45130e5da6a5dce31"
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

def get_location():
    """Uses geocoder to get the user's current latitude and longitude."""
    g = geocoder.ip("me")  # Gets location based on public IP
    if g.ok:
        return g.latlng  # Returns [latitude, longitude]
    else:
        print("❌ Error getting location.")
        return None

def get_weather(lat, lon):
    """Fetches weather data for given latitude and longitude."""
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric"  # Get temperature in Celsius
    }

    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()

        weather_desc = data["weather"][0]["description"].title()
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        city_name = data["name"]
        country = data["sys"]["country"]

        print(f"\n📍 Location: {city_name}, {country}")
        print(f"🌤 Weather: {weather_desc}")
        print(f"🌡 Temperature: {temp}°C")
        print(f"💧 Humidity: {humidity}%")
        print(f"💨 Wind Speed: {wind_speed} m/s")
    
    else:
        print("❌ Error fetching weather data.")

if __name__ == "__main__":
    location = get_location()
    if location:
        lat, lon = location
        print(f"🔎 Detected Location: {lat}, {lon}")
        get_weather(lat, lon)
    else:
        print("❌ Could not detect location.")
