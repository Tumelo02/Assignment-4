from flask import Flask, request, jsonify
from flask_cors import CORS
import time

# === Flask App Initialization ===
app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from frontend (Flet or browser apps)

# === In-Memory Sensor Data Storage ===
sensor_data = {
    "moisture": 0,        # Raw value from soil moisture sensor (range: 0 to 4095)
    "rain": 0,            # Rain sensor status (0 = no rain, 1 = raining)
    "timestamp": None     # Timestamp of the latest sensor update
}

# === Control State (from frontend or auto logic) ===
control_state = {
    "pump": 0,            # Pump manual override (1 = force ON, 0 = auto)
    "angle": 90,          # Servo angle for sprinkler direction (0° to 180°)
    "mode": "auto"        # "manual" or "auto"                     
}

# === Moisture Calibration and Thresholds ===
MOISTURE_MIN = 0               # Sensor value when soil is fully wet
MOISTURE_MAX = 4095            # Sensor value when soil is fully dry
DRY_THRESHOLD_PERCENT = 40     # If moisture % falls below this, auto mode turns pump ON

# === Endpoint: Receive Sensor Data from Microcontroller ===
@app.route("/data", methods=["POST"])
def receive_data():
    data = request.get_json()

    # Update sensor readings
    sensor_data["moisture"] = data.get("moisture", 0)
    sensor_data["rain"] = data.get("rain", 0)
    sensor_data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

    print(f"[DATA RECEIVED] {sensor_data}")
    return jsonify({"status": "success"}), 200

# === Endpoint: Get or Update Manual Control Settings ===
@app.route("/control", methods=["GET", "POST"])
def control():
    if request.method == "GET":
        return jsonify(control_state), 200

    data = request.get_json()
    control_state["pump"] = data.get("pump", control_state["pump"])
    control_state["angle"] = data.get("angle", control_state["angle"])
    control_state["mode"] = data.get("mode", control_state["mode"])  # NEW

    print(f"[CONTROL UPDATED] {control_state}")
    return jsonify({"status": "updated"}), 200

# === Endpoint: Return System Status (moisture %, rain, pump status, etc.) ===
@app.route("/status", methods=["GET"])
def status():
    # === Calculate Moisture Percentage ===
    raw = sensor_data["moisture"]
    percent = int(100 - ((raw - MOISTURE_MIN) / (MOISTURE_MAX - MOISTURE_MIN)) * 100)
    percent = max(0, min(percent, 100))  # Clamp to 0–100%

    # === Auto Mode Logic (with Rain Override) ===
    if control_state["mode"] == "auto":
        if sensor_data["rain"] == 1:
            control_state["pump"] = 0  # Disable pump if raining
            print("[AUTO MODE] Rain detected — pump disabled.")
        else:
            if percent < DRY_THRESHOLD_PERCENT:
                control_state["pump"] = 1
                print("[AUTO MODE] Soil dry — pump enabled.")
            else:
                control_state["pump"] = 0
                print("[AUTO MODE] Soil moist — pump disabled.")

    return jsonify({
        "moisture": raw,
        "moisture_percent": percent,
        "rain": sensor_data["rain"],
        "pump_status": control_state["pump"],
        "angle": control_state["angle"],
        "mode": control_state["mode"]
    }), 200

# === Run Flask App ===
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")