import network
import urequests
import time
from machine import Pin, ADC, PWM

# === WiFi Credentials ===
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

# === Backend Configuration ===
BACKEND_HOST = "http://192.168.231.47:5000"  # Update if IP changes
POST_DATA_URL = f"{BACKEND_HOST}/data"
GET_CONTROL_URL = f"{BACKEND_HOST}/control"

# === GPIO Pin Setup ===
soil_moi_pin = ADC(Pin(34))           # A0 - Soil moisture sensor
soil_moi_pin.atten(ADC.ATTN_11DB)     # Full 0–3.3V range

rain_sen = Pin(18, Pin.IN)            # D18 - Rain sensor
water_pum = Pin(22, Pin.OUT)          # D22 - Relay for water pump
servo = PWM(Pin(21), freq=50)         # D21 - Servo motor (angle control)

# === Moisture Threshold for Auto Mode ===
dry_threshold = 2000  # Adjust based on testing

# === Helper Functions ===

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    print("Connecting to WiFi", end="")
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.5)
    print("\nConnected:", wlan.ifconfig())

def angle_to_duty(angle):
    # Convert angle (0–180) to PWM duty (typically 26–128)
    return int((angle / 180) * 102 + 26)

def send_sensor_data(moisture, rain):
    try:
        response = urequests.post(POST_DATA_URL, json={
            "moisture": moisture,
            "rain": rain
        })
        response.close()
    except Exception as e:
        print("Failed to POST data:", e)

def get_controls():
    try:
        response = urequests.get(GET_CONTROL_URL)
        if response.status_code == 200:
            data = response.json()
            return data.get("pump", 0), data.get("angle", 90)
        response.close()
    except Exception as e:
        print("Failed to GET control:", e)
    return 0, 90  # Fallback values

# === Main Loop ===

def run():
    connect_wifi()

    while True:
        # Read sensors
        moisture_value = soil_moi_pin.read()
        rain_detected = 1 if rain_sen.value() == 0 else 0  # Active LOW

        print("Moisture:", moisture_value, "| Rain:", rain_detected)

        # Send sensor data to backend
        send_sensor_data(moisture_value, rain_detected)

        # Get user control settings
        pump_state, angle = get_controls()

        # === Pump Decision Logic ===
        if pump_state == 1:
            # Manual ON by user
            water_pum.value(1)
            print("Pump: Forced ON by user")
        else:
            # Auto mode based on soil moisture
            if moisture_value < dry_threshold:
                water_pum.value(1)
                print("Pump: ON (Auto - Soil is dry)")
            else:
                water_pum.value(0)
                print("Pump: OFF (Auto - Soil is wet)")

        # Set servo angle
        servo.duty(angle_to_duty(angle))

        time.sleep(5)  # Delay between cycles

# === Start Program ===
run()