import network
import urequests
import time
from machine import Pin, ADC, PWM

# === WiFi Configuration ===
SSID = "A15"             # WiFi name
PASSWORD = "12345678"    # WiFi password

# === Backend Server URLs ===
BACKEND_HOST = "http://192.168.231.47:5000"  # Flask backend IP
POST_DATA_URL = f"{BACKEND_HOST}/data"       # Endpoint for sending sensor data
GET_CONTROL_URL = f"{BACKEND_HOST}/control"  # Endpoint for receiving control data

# === GPIO Pin Setup ===
soil_sensor = ADC(Pin(34))           # Soil moisture sensor on ADC pin
soil_sensor.atten(ADC.ATTN_11DB)     # Set ADC range to 0-3.3V

rain_sensor = Pin(18, Pin.IN)        # Rain sensor digital input (LOW = rain)
pump = Pin(22, Pin.OUT)              # Water pump relay output
servo = PWM(Pin(21), freq=50)        # Servo for sprinkler angle

# === System Constants ===
DRY_THRESHOLD = 2000                 # Moisture reading below this = dry soil

# === Helper Function: Convert angle to PWM duty cycle for servo ===
def angle_to_duty(angle):
    # Maps 0–180 degrees to servo PWM duty (typical servo range)
    return int((angle / 180) * 102 + 26)

# === Connect to WiFi ===
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    print("Connecting to WiFi", end="")
    timeout = 10
    start = time.time()

    while not wlan.isconnected():
        if time.time() - start > timeout:
            print("\nFailed to connect: Timeout")
            return False
        print(".", end="")
        time.sleep(1)

    print("\nConnected to WiFi:", wlan.ifconfig())
    return True

# === Send sensor readings to Flask backend ===
def send_sensor_data(moisture, rain):
    try:
        payload = {"moisture": moisture, "rain": rain}
        response = urequests.post(POST_DATA_URL, json=payload)
        response.close()
        print("Sent sensor data:", payload)
    except Exception as e:
        print("Failed to POST data:", e)

# === Get control settings from backend ===
def get_controls():
    try:
        response = urequests.get(GET_CONTROL_URL)
        if response.status_code == 200:
            data = response.json()
            pump_state = data.get("pump", 0)
            angle = data.get("angle", 90)
            mode = data.get("mode", "auto")  
            response.close()
            return pump_state, angle, mode
    except Exception as e:
        print("Failed to GET controls:", e)
    return 0, 90, "auto"  # Fallback defaults

# === Main Loop ===
def run():
    if not connect_wifi():
        return  # Stop if WiFi failed

    while True:
        # === Step 1: Read Sensors ===
        moisture = soil_sensor.read()              # Raw analog value
        rain = 1 if rain_sensor.value() == 0 else 0  # Active LOW = Rain Detected

        print(f"\nMoisture: {moisture} | Rain: {'Yes' if rain else 'No'}")

        # === Step 2: Send Sensor Data to Backend ===
        send_sensor_data(moisture, rain)

        # === Step 3: Receive Controls from Backend ===
        pump_state, angle, mode = get_controls()
        print(f"Mode: {mode} | Pump (Manual): {pump_state} | Sprinkler Angle: {angle}°")

        # === Pump Control Logic ===
        if mode == "manual":
        # User manually controls pump
            pump.value(1 if pump_state == 1 else 0)
            print("Pump: Manual", "ON" if pump_state else "OFF")
        else:
            # Auto mode: Pump turns ON if soil is dry (moisture reading HIGH)
            if moisture > DRY_THRESHOLD:
                pump.value(1)
                print("Pump: ON (Auto - Soil is dry)")
            else:
                pump.value(0)
                print("Pump: OFF (Auto - Soil is wet)")

        # === Step 5: Move Servo to Desired Angle ===
        servo.duty(angle_to_duty(angle))
        print(f"Sprinkler moved to {angle}°")

        time.sleep(5)  # Delay between each update

# === Start System ===
run()