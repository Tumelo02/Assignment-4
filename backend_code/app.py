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
    "angle": 90           # Servo angle for sprinkler direction (0° to 180°)
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
        # Return current control settings (used by frontend)
        return jsonify(control_state), 200

    # Update control settings (pump override or sprinkler angle)
    data = request.get_json()
    control_state["pump"] = data.get("pump", control_state["pump"])
    control_state["angle"] = data.get("angle", control_state["angle"])

    print(f"[CONTROL UPDATED] {control_state}")
    return jsonify({"status": "updated"}), 200

# === Endpoint: Return System Status (moisture %, rain, pump status, etc.) ===
@app.route("/status", methods=["GET"])
def status():
    raw_moisture = sensor_data.get("moisture", 0)
    manual_override = control_state["pump"]

    # === Calculate Moisture Percentage ===
    # 100% = very wet (0), 0% = very dry (4095)
    clamped = min(max(raw_moisture, MOISTURE_MIN), MOISTURE_MAX)
    moisture_percent = 100 - int((clamped - MOISTURE_MIN) / (MOISTURE_MAX - MOISTURE_MIN) * 100)
    moisture_percent = max(0, min(moisture_percent, 100))  # Clamp to 0–100%

    # === Determine Pump Status (manual override vs auto logic) ===
    if manual_override == 1:
        pump_status = 1
        mode = "manual"
    else:
        pump_status = 1 if moisture_percent < DRY_THRESHOLD_PERCENT else 0
        mode = "auto"

    # Debug Output
    print(f"[STATUS CHECK] Moisture Raw: {raw_moisture}, Moisture %: {moisture_percent}, Mode: {mode}, Pump: {'ON' if pump_status else 'OFF'}")

    # === Return JSON Status Response to Frontend ===
    return jsonify({
        "moisture": raw_moisture,
        "moisture_percent": moisture_percent,
        "rain": sensor_data["rain"],
        "timestamp": sensor_data["timestamp"],
        "pump_status": pump_status,
        "mode": mode,
        "angle": control_state["angle"]
    }), 200

# === Entry Point: Start Flask App ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)