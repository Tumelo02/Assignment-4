import network
import urequests
import time
from machine import Pin, ADC, PWM

# WiFi Credentials
SSID = "A15"
PASSWORD = "12345678"

wifi = network.WLAN(network.STA_IF)
wifi.active(True)

print("Connecting to WiFi...")

wifi.connect(SSID, PASSWORD)

# Wait for the connection
timeout = 10  # seconds
start_time = time.time()
while not wifi.isconnected():
    if time.time() - start_time > timeout:
        print("Connection failed! Timeout.")
        break
    time.sleep(1)

if wifi.isconnected():
    print("WiFi connected!")
    print(wifi.ifconfig())  # Print IP address
else:
    print("Failed to connect to WiFi")

# Flask API Endpoints
BACKEND_HOST = "http://127.0.0.1:5000"
POST_DATA_URL = f"{BACKEND_HOST}/data"
GET_CONTROL_URL = f"{BACKEND_HOST}/control"

# GPIO Pins
soil_moisture_pin = ADC(Pin(34))      # A0
soil_moisture_pin.atten(ADC.ATTN_11DB)  # Full range: 0-3.3V

rain_sensor = Pin(18, Pin.IN)         # D5
water_pump = Pin(22, Pin.OUT)         # D22 (Relay)
servo = PWM(Pin(21), freq=50)         # D21 (Servo PWM)

# Helper: Connect to WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    print("Connecting to WiFi", end="")
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.5)
    print("\nConnected:", wlan.ifconfig())

# Map degrees to PWM duty
def angle_to_duty(angle):
    return int((angle / 180) * 102 + 26)  # 0° ~ 26, 180° ~ 128

# Send sensor data to Flask backend
def send_sensor_data(moisture, rain):
    try:
        response = urequests.post(POST_DATA_URL, json={
            "moisture": moisture,
            "rain": rain
        })
        response.close()
    except Exception as e:
        print("Failed to POST data:", e)

# Fetch control commands
def get_controls():
    try:
        response = urequests.get(GET_CONTROL_URL)
        if response.status_code == 200:
            data = response.json()
            return data.get("pump", 0), data.get("angle", 90)
        response.close()
    except Exception as e:
        print("Failed to GET control:", e)
    return 0, 90  # Defaults

# Main loop
def run():
    connect_wifi()

    while True:
        # Read sensors
        moisture_value = soil_moisture_pin.read()
        rain_detected = 1 if rain_sensor.value() == 0 else 0  # active LOW

        print("Moisture:", moisture_value, "| Rain:", rain_detected)

        # Send data
        send_sensor_data(moisture_value, rain_detected)

        # Get control instructions
        pump_state, angle = get_controls()

        # Apply controls
        water_pump.value(pump_state)
        servo.duty(angle_to_duty(angle))

        time.sleep(5)  # Delay between cycles

run()